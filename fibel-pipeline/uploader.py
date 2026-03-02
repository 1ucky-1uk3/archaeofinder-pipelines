"""
ArchaeoFinder Fibel-Pipeline v2.1.1 — Supabase Uploader
=========================================================
FIX: 409 Conflict → Korrektes UPSERT mit on_conflict Parameter.

PostgREST braucht BEIDES:
  1. UNIQUE constraint auf (source, source_id) in der DB
  2. on_conflict=source,source_id in der URL
  3. Prefer: resolution=merge-duplicates im Header

Ohne on_conflict gibt PostgREST 409 statt UPSERT.
"""

import asyncio
import json
import logging
from typing import List, Dict

import httpx
from rich.console import Console

import config

logger = logging.getLogger("fibel-pipeline")
console = Console()


class SupabaseUploader:
    """Batch-Upload zu Supabase mit korrektem UPSERT."""

    def __init__(self):
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_SERVICE_KEY
        self.table = config.SUPABASE_TABLE

        if not self.key:
            raise ValueError(
                "SUPABASE_SERVICE_KEY nicht gesetzt!\n"
                "Benoetigt Service Role Key (nicht anon key).\n"
                "Setze: export SUPABASE_SERVICE_KEY=eyJ..."
            )

    async def ensure_unique_constraint(self):
        """Stellt sicher, dass der UNIQUE constraint existiert."""
        console.print("  Pruefe UNIQUE constraint...")
        sql = """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'fibula_embeddings_source_source_id_unique'
            ) THEN
                ALTER TABLE fibula_embeddings
                ADD CONSTRAINT fibula_embeddings_source_source_id_unique
                UNIQUE (source, source_id);
                RAISE NOTICE 'UNIQUE constraint erstellt';
            END IF;
        END $$;
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.url}/rest/v1/rpc/exec_sql",
                    json={"query": sql},
                    headers={
                        "apikey": self.key,
                        "Authorization": f"Bearer {self.key}",
                        "Content-Type": "application/json",
                    }
                )
                # Falls RPC nicht existiert, versuche direkt
                if resp.status_code != 200:
                    console.print("  [yellow]RPC nicht verfuegbar — UNIQUE constraint manuell pruefen![/yellow]")
                    console.print("  [yellow]SQL ausfuehren:[/yellow]")
                    console.print("  [dim]ALTER TABLE fibula_embeddings ADD CONSTRAINT fibula_embeddings_source_source_id_unique UNIQUE (source, source_id);[/dim]")
                else:
                    console.print("  [green]UNIQUE constraint OK[/green]")
        except Exception:
            console.print("  [yellow]Constraint-Check uebersprungen[/yellow]")

    async def upload_batch(self, items: List[Dict], batch_size: int = None):
        """Items in Batches zu Supabase hochladen (UPSERT)."""
        batch_size = batch_size or config.UPLOAD_BATCH_SIZE

        console.print(f"\n[bold cyan]=== PHASE 3: SUPABASE UPLOAD ===[/bold cyan]")
        console.print(f"  Items: {len(items)} | Batch: {batch_size} | Tabelle: {self.table}")
        console.print(f"  Modus: UPSERT (on_conflict=source,source_id)")

        # Versuche constraint sicherzustellen
        await self.ensure_unique_constraint()

        uploaded = 0
        updated = 0
        errors = 0
        first_error_logged = False

        # ── UPSERT URL mit on_conflict ──
        upsert_url = f"{self.url}/rest/v1/{self.table}?on_conflict=source,source_id"

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                rows = [self._prepare_row(item) for item in batch]

                try:
                    response = await client.post(
                        upsert_url,
                        json=rows,
                        headers={
                            "apikey": self.key,
                            "Authorization": f"Bearer {self.key}",
                            "Content-Type": "application/json",
                            "Prefer": "resolution=merge-duplicates,return=minimal",
                        }
                    )

                    if response.status_code in (200, 201):
                        uploaded += len(batch)
                    elif response.status_code == 409:
                        # Immer noch 409? → Constraint fehlt, Fallback: Einzeln einfuegen
                        if not first_error_logged:
                            logger.warning(f"409 trotz on_conflict — Fallback auf Einzel-Insert")
                            console.print("  [yellow]409 Conflict — Versuche Einzel-Inserts...[/yellow]")
                            first_error_logged = True
                        single_ok, single_skip = await self._insert_singles(client, rows)
                        uploaded += single_ok
                        updated += single_skip
                    else:
                        errors += len(batch)
                        if not first_error_logged:
                            logger.error(f"Upload: HTTP {response.status_code} — {response.text[:300]}")
                            first_error_logged = True

                except Exception as e:
                    errors += len(batch)
                    logger.error(f"Upload exception: {e}")

                await asyncio.sleep(0.1)

                batch_num = i // batch_size
                if batch_num % 5 == 0:
                    pct = min(i + batch_size, len(items))
                    console.print(f"  Progress: {pct}/{len(items)} (neu: {uploaded}, updated: {updated}, err: {errors})")

        console.print(f"\n  [bold green]✓ Upload abgeschlossen[/bold green]")
        console.print(f"  Neu: {uploaded} | Updated: {updated} | Fehler: {errors}")

        return {"uploaded": uploaded, "updated": updated, "errors": errors}

    async def _insert_singles(self, client, rows):
        """Fallback: Einzeln einfuegen, bei Conflict updaten."""
        ok = 0
        skip = 0
        for row in rows:
            try:
                # Versuche INSERT
                resp = await client.post(
                    f"{self.url}/rest/v1/{self.table}",
                    json=row,
                    headers={
                        "apikey": self.key,
                        "Authorization": f"Bearer {self.key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    }
                )
                if resp.status_code in (200, 201):
                    ok += 1
                elif resp.status_code == 409:
                    # Existiert schon → PATCH (Update)
                    patch_resp = await client.patch(
                        f"{self.url}/rest/v1/{self.table}"
                        f"?source=eq.{row['source']}&source_id=eq.{row['source_id']}",
                        json={k: v for k, v in row.items() if k not in ("source", "source_id")},
                        headers={
                            "apikey": self.key,
                            "Authorization": f"Bearer {self.key}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal",
                        }
                    )
                    if patch_resp.status_code in (200, 204):
                        skip += 1
            except Exception:
                pass
        return ok, skip

    def _prepare_row(self, item: Dict) -> Dict:
        """Item fuer Supabase vorbereiten."""
        return {
            "source": item["source"],
            "source_id": item["source_id"],
            "title": item.get("title", "")[:500],
            "description": item.get("description", "")[:2000],
            "image_url": item["image_url"],
            "thumbnail_url": item.get("thumbnail_url", ""),
            "source_url": item.get("source_url", ""),
            "museum": item.get("museum", ""),
            "epoch": item.get("epoch", ""),
            "material": item.get("material", ""),
            "region": item.get("region", ""),
            "fibula_type": item.get("fibula_type", ""),
            "metadata": json.dumps({
                "search_query": item.get("search_query", ""),
                "pipeline_version": config.PIPELINE_VERSION,
            }),
            "embedding": item["embedding"],
            "image_hash": item.get("image_hash", ""),
            "pipeline_version": config.PIPELINE_VERSION,
            "embedding_model": f"{config.CLIP_MODEL}/{config.CLIP_PRETRAINED}",
        }
