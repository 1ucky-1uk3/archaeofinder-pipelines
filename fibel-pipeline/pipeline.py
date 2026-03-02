#!/usr/bin/env python3
"""
ArchaeoFinder — Fibel-Pipeline v4.0.0 (Orchestrator)
=====================================================
UPGRADE: ViT-L-14-336 @ 336px

Identische Architektur wie v3.5.1, nur mit neuem Modell.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
import traceback
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import config

_log_handlers = [logging.StreamHandler()]
_log_dir = Path("/app/logs")
if _log_dir.exists():
    _log_handlers.append(logging.FileHandler(_log_dir / "pipeline.log"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_log_handlers
)
logger = logging.getLogger("fibel-pipeline")
console = Console()

DATA_DIR = Path("/app/data")
CACHE_DIR = DATA_DIR / "cache"
COLLECTED_FILE = CACHE_DIR / "collected_items.json"
EMBEDDED_FILE = CACHE_DIR / "embedded_items.json"
PARTIAL_FILE = CACHE_DIR / "embedded_items_partial.json"

for d in [DATA_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# =============================================================================
# PHASE 1: SAMMELN
# =============================================================================

async def run_collect():
    from museum_apis import MuseumCollector
    collector = MuseumCollector()
    items = await collector.collect_all()
    with open(COLLECTED_FILE, "w") as f:
        json.dump(items, f)
    console.print(f"  Cache: {COLLECTED_FILE} ({len(items):,} Fibeln)")
    return items


# =============================================================================
# PHASE 2: GPU EMBEDDING (ViT-L-14-336 @ 336px)
# =============================================================================

async def run_embed(items):
    from embedder import GPUEmbedder

    embedder = GPUEmbedder()
    embedder.load_model()

    try:
        results = await embedder.process_items(items)
    except Exception as e:
        logger.error(f"EMBEDDING CRASH: {e}\n{traceback.format_exc()}")
        console.print(f"\n  [bold red]Embedding-Fehler: {e}[/bold red]")

        if PARTIAL_FILE.exists():
            console.print(f"  Lade Partial-Ergebnisse aus {PARTIAL_FILE}...")
            with open(PARTIAL_FILE) as f:
                results = json.load(f)
            console.print(f"  {len(results):,} Partial-Embeddings gerettet")
        else:
            results = []
            console.print(f"  [yellow]Keine Partial-Ergebnisse vorhanden[/yellow]")

    if results:
        with open(EMBEDDED_FILE, "w") as f:
            json.dump(results, f)
        console.print(f"  Cache: {EMBEDDED_FILE} ({len(results):,} Embeddings)")
    else:
        console.print(f"  [bold red]0 Embeddings — pruefe Logfile[/bold red]")

    return results


# =============================================================================
# PHASE 3: UPLOAD
# =============================================================================

async def run_upload(items):
    from uploader import SupabaseUploader
    uploader = SupabaseUploader()
    return await uploader.upload_batch(items)


# =============================================================================
# STATS
# =============================================================================

async def run_stats():
    console.print("\n[bold cyan]=== PIPELINE STATISTIKEN ===[/bold cyan]\n")

    if COLLECTED_FILE.exists():
        with open(COLLECTED_FILE) as f:
            collected = json.load(f)
        console.print(f"  Gesammelt: {len(collected):,} Items")
        sources = {}
        for item in collected:
            sources[item["source"]] = sources.get(item["source"], 0) + 1
        table = Table(title="Quellen")
        table.add_column("Quelle", style="cyan")
        table.add_column("Anzahl", style="green", justify="right")
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            table.add_row(src, f"{count:,}")
        console.print(table)
    else:
        console.print("  [yellow]Keine Sammlung vorhanden[/yellow]")

    if EMBEDDED_FILE.exists():
        with open(EMBEDDED_FILE) as f:
            embedded = json.load(f)
        console.print(f"\n  Embeddings: {len(embedded):,} ({config.EMBEDDING_DIM}d)")
        console.print(f"  Modell: {config.CLIP_MODEL} @ {config.IMAGE_SIZE}px")
    else:
        console.print("  [yellow]Keine Embeddings vorhanden[/yellow]")

    if PARTIAL_FILE.exists():
        with open(PARTIAL_FILE) as f:
            partial = json.load(f)
        console.print(f"  Partial:    {len(partial):,} (von letztem Crash)")


# =============================================================================
# HAUPTPROGRAMM
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="ArchaeoFinder Fibel-Pipeline v4.0.0")
    parser.add_argument("--mode", choices=["full", "collect", "embed", "upload", "stats"],
                        default="full", help="Pipeline-Modus")
    args = parser.parse_args()

    console.print(Panel(
        f"  ARCHAEOFINDER  Fibel-Pipeline  v{config.PIPELINE_VERSION}\n"
        f"   CLIP {config.CLIP_MODEL} @ {config.IMAGE_SIZE}px "
        f"({config.EMBEDDING_DIM}d) — 576 Patches\n"
        f"   Robust + GPU-Optimiert + Dynamische Batch-Groesse\n"
        f"   Modus: {args.mode.upper()}",
        border_style="bright_magenta"
    ))

    start = time.time()

    if args.mode == "stats":
        await run_stats()
        return

    # ─── Phase 1: Sammeln ───
    if args.mode in ("full", "collect"):
        console.print("\n[bold]── PHASE 1: FIBELN SAMMELN ──[/bold]\n")
        try:
            items = await run_collect()
        except Exception as e:
            logger.error(f"SAMMLUNG CRASH: {e}\n{traceback.format_exc()}")
            console.print(f"\n  [bold red]Sammlungs-Fehler: {e}[/bold red]")
            return
    elif COLLECTED_FILE.exists():
        with open(COLLECTED_FILE) as f:
            items = json.load(f)
        console.print(f"  Lade {len(items):,} gecachte Fibeln...")
    else:
        console.print("[red]Keine gesammelten Daten. Bitte zuerst --mode collect[/red]")
        return

    if args.mode == "collect":
        elapsed = time.time() - start
        m, s = divmod(int(elapsed), 60)
        console.print(f"\n[bold green]Sammlung fertig in {m}m {s}s[/bold green]\n")
        return

    # ─── Phase 2: Embedden (ViT-L-14-336 @ 336px) ───
    if args.mode in ("full", "embed"):
        console.print("\n[bold]── PHASE 2: GPU EMBEDDING (ViT-L-14-336 @ 336px) ──[/bold]\n")
        embedded = await run_embed(items)
    elif EMBEDDED_FILE.exists():
        with open(EMBEDDED_FILE) as f:
            embedded = json.load(f)
        console.print(f"  Lade {len(embedded):,} gecachte Embeddings...")
    else:
        console.print("[red]Keine Embeddings. Bitte zuerst --mode embed[/red]")
        return

    if args.mode == "embed":
        elapsed = time.time() - start
        m, s = divmod(int(elapsed), 60)
        console.print(f"\n[bold green]Embedding fertig in {m}m {s}s[/bold green]\n")
        return

    # ─── Phase 3: Upload ───
    if not embedded:
        console.print("[bold red]0 Embeddings — Upload uebersprungen[/bold red]")
    elif args.mode in ("full", "upload"):
        console.print("\n[bold]── PHASE 3: SUPABASE UPLOAD ──[/bold]\n")
        try:
            await run_upload(embedded)
        except Exception as e:
            logger.error(f"UPLOAD CRASH: {e}\n{traceback.format_exc()}")
            console.print(f"\n  [bold red]Upload-Fehler: {e}[/bold red]")
            console.print(f"  [yellow]Embeddings gespeichert in {EMBEDDED_FILE}[/yellow]")
            console.print(f"  [yellow]Erneut starten mit: --mode upload[/yellow]")

    elapsed = time.time() - start
    m, s = divmod(int(elapsed), 60)
    console.print(f"\n[bold green]Pipeline abgeschlossen in {m}m {s}s[/bold green]\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline abgebrochen (Ctrl+C)[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"FATALER FEHLER: {e}\n{traceback.format_exc()}")
        console.print(f"\n[bold red]FATALER FEHLER: {e}[/bold red]")
        console.print(f"[dim]Details im Logfile: /app/logs/pipeline.log[/dim]")
        sys.exit(1)