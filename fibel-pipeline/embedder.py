"""
ArchaeoFinder Fibel-Pipeline v4.0.0 — GPU CLIP Embedder
========================================================
UPGRADE: ViT-L-14-336 @ 336px (vorher ViT-L-14 @ 224px)

Aenderungen gegenueber v3.5.1:
  1. Modell: ViT-L-14-336 statt ViT-L-14
  2. IMAGE_SIZE: 336px statt 224px
  3. Batch: 128 default (statt 256) wg. hoeherer VRAM-Nutzung
  4. Dynamische Batch-Groesse bei OOM
  5. Image-Quality: JPEG q90 im Cache (statt q85)
  6. Min-Image-Size: 2000 bytes (statt 1000)
  7. VRAM-Monitoring mit Peak-Tracking
"""

import asyncio
import hashlib
import io
import json
import logging
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

import aiohttp
import numpy as np
from PIL import Image
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

import config

logger = logging.getLogger("fibel-pipeline")
console = Console()

IMAGES_DIR = Path(config.IMAGES_DIR)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

BAD_URL_PATTERNS = [
    "placeholder", "no_image", "noimage", "default.jpg", "dummy",
    "spacer.gif", "blank.png", "missing.jpg", "default_thumbnail",
    "icon_nophoto",
]

_WORKER_DONE = object()


class GPUEmbedder:
    """CLIP ViT-L-14-336 @ 336px — Robuste GPU-Pipeline v4.0.0.

    NEU in v4.0.0:
      - ViT-L-14-336: 576 Patches statt 256 (2.25x mehr Detail)
      - Dynamische Batch-Groesse bei OOM
      - Hoehere Bildqualitaet im Cache (q90)
      - VRAM-Monitoring mit Peak-Tracking
    """

    def __init__(self):
        self.model = None
        self.preprocess = None
        self.device = None
        self._preprocess_pool = None
        self._domain_stats = defaultdict(lambda: {"ok": 0, "fail": 0})
        self._current_batch_size = config.BATCH_SIZE
        self._peak_vram = 0.0

    # ─── Model ────────────────────────────────────────────────────────

    def load_model(self):
        """CLIP ViT-L-14-336 laden mit CUDA-Optimierungen."""
        import torch
        import open_clip

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9

            # Empfohlene Batch-Groesse basierend auf VRAM
            if gpu_mem < 8:
                recommended_batch = 64
            elif gpu_mem < 12:
                recommended_batch = 128
            elif gpu_mem < 24:
                recommended_batch = 192
            else:
                recommended_batch = 256

            if config.BATCH_SIZE > recommended_batch:
                logger.warning(
                    f"BATCH_SIZE={config.BATCH_SIZE} hoch fuer {gpu_mem:.1f}GB VRAM. "
                    f"Empfohlen: {recommended_batch}. Dynamische Anpassung aktiv."
                )

            console.print(Panel(
                f"  Geraet:   [yellow]CUDA[/yellow]  ({gpu_name}, {gpu_mem:.1f} GB)\n"
                f"  Modell:   [cyan]{config.CLIP_MODEL}[/cyan] ({config.EMBEDDING_DIM}d) "
                f"@ [bold green]{config.IMAGE_SIZE}px[/bold green]\n"
                f"  Patches:  [green]24x24 = 576[/green] (vs 16x16 = 256 bei 224px)\n"
                f"  Batch:    [cyan]{config.BATCH_SIZE}[/cyan]  Workers: [cyan]{config.MAX_WORKERS}[/cyan]  "
                f"Preproc: [cyan]{getattr(config, 'PREPROCESS_THREADS', 8)}T[/cyan]\n"
                f"  Empf.:    Batch <={recommended_batch} fuer {gpu_mem:.1f}GB\n"
                f"  Features: OOM-Recovery + Pinned-Memory + TF32 + Adaptive-Flush\n"
                f"           Dynamische Batch-Groesse + VRAM-Monitoring",
                title="CLIP Modell v4.0.0 — ViT-L-14-336", border_style="bright_green"
            ))
        else:
            console.print(f"  [yellow]WARNUNG: Kein CUDA — CPU (336px sehr langsam!)[/yellow]")

        # ViT-L-14-336 laden — open_clip setzt Transforms automatisch auf 336px
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            config.CLIP_MODEL, pretrained=config.CLIP_PRETRAINED, device=self.device
        )
        self.model.eval()

        n_threads = getattr(config, 'PREPROCESS_THREADS', 8)
        self._preprocess_pool = ThreadPoolExecutor(max_workers=n_threads)

        logger.info(
            f"CLIP Model geladen: {config.CLIP_MODEL} ({config.EMBEDDING_DIM}d) "
            f"@ {config.IMAGE_SIZE}px auf {self.device}"
        )
        console.print(f"  [green]Modell geladen: {config.CLIP_MODEL} @ {config.IMAGE_SIZE}px[/green]")

    # ─── URL Filtering ────────────────────────────────────────────────

    def _is_bad_url(self, url):
        return any(p in url.lower() for p in BAD_URL_PATTERNS)

    def _check_domain(self, url):
        try:
            d = urlparse(url).netloc
        except Exception:
            return False
        s = self._domain_stats[d]
        t = s["ok"] + s["fail"]
        return not (t >= 20 and s["fail"] / t > 0.80)

    def _track_domain(self, url, ok):
        try:
            self._domain_stats[urlparse(url).netloc]["ok" if ok else "fail"] += 1
        except Exception:
            pass

    # ─── VRAM Monitoring ──────────────────────────────────────────────

    def _update_vram(self):
        import torch
        if self.device == "cuda":
            try:
                current = torch.cuda.memory_allocated() / 1e9
                if current > self._peak_vram:
                    self._peak_vram = current
            except Exception:
                pass

    def _get_vram_info(self):
        import torch
        if self.device != "cuda":
            return "CPU"
        try:
            alloc = torch.cuda.memory_allocated() / 1e9
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            return f"{alloc:.1f}/{total:.1f}GB (Peak: {self._peak_vram:.1f}GB)"
        except Exception:
            return "N/A"

    # ─── Download ─────────────────────────────────────────────────────

    async def download_image(self, session, url, item_id):
        """Bild herunterladen mit Disk-Cache und Domain-Health.
        v4.0.0: JPEG q90, min 2000 bytes fuer 336px Qualitaet.
        """
        if self._is_bad_url(url) or not self._check_domain(url):
            return None

        cache_path = IMAGES_DIR / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"
        if cache_path.exists():
            try:
                img = Image.open(cache_path).convert("RGB")
                self._track_domain(url, True)
                return img
            except Exception:
                cache_path.unlink(missing_ok=True)

        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=config.DOWNLOAD_TIMEOUT)
            ) as resp:
                if resp.status != 200:
                    self._track_domain(url, False)
                    return None
                cl = resp.headers.get("Content-Length", "0")
                if cl.isdigit() and int(cl) > config.MAX_IMAGE_SIZE_MB * 1024 * 1024:
                    self._track_domain(url, False)
                    return None
                data = await resp.read()
                # v4.0.0: Mindestgroesse 2000 bytes (336px braucht mehr Detail)
                if len(data) < 2000:
                    self._track_domain(url, False)
                    return None
                img = Image.open(io.BytesIO(data)).convert("RGB")
                # v4.0.0: Hoehere Cache-Qualitaet fuer 336px
                img.save(cache_path, "JPEG", quality=90)
                self._track_domain(url, True)
                return img
        except Exception:
            self._track_domain(url, False)
            return None

    # ─── GPU Embedding ────────────────────────────────────────────────

    def embed_batch(self, images):
        """Batch embedden — 336px Tensoren: [B, 3, 336, 336] = 2.25x groesser."""
        import torch

        futures = [self._preprocess_pool.submit(self.preprocess, img) for img in images]
        tensors = torch.stack([f.result() for f in futures])

        if self.device == "cuda":
            tensors = tensors.pin_memory().to(self.device, non_blocking=True)
            with torch.no_grad(), torch.amp.autocast("cuda"):
                emb = self.model.encode_image(tensors)
                emb = emb / emb.norm(dim=-1, keepdim=True)
            self._update_vram()
        else:
            tensors = tensors.to(self.device)
            with torch.no_grad():
                emb = self.model.encode_image(tensors)
                emb = emb / emb.norm(dim=-1, keepdim=True)

        return emb.cpu().numpy().astype(np.float32)

    def embed_batch_safe(self, images):
        """Embed mit OOM-Recovery und dynamischer Batch-Anpassung.
        v4.0.0: Bei OOM wird batch_size halbiert fuer nachfolgende Batches.
        """
        import torch

        try:
            return self.embed_batch(images)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            old_batch = self._current_batch_size
            self._current_batch_size = max(8, self._current_batch_size // 2)
            logger.warning(
                f"OOM bei Batch={len(images)}! "
                f"Batch-Groesse: {old_batch} -> {self._current_batch_size}. "
                f"Versuche in Haelften..."
            )
            mid = len(images) // 2
            if mid == 0:
                logger.error("Einzelbild verursacht OOM — uebersprungen")
                return None
            r1 = self.embed_batch_safe(images[:mid])
            r2 = self.embed_batch_safe(images[mid:])
            if r1 is not None and r2 is not None:
                return np.concatenate([r1, r2])
            return r1 if r1 is not None else r2
        except Exception as e:
            logger.error(f"Embed-Fehler (kein OOM): {e}")
            return None

    # ─── Status Display ───────────────────────────────────────────────

    def _status_line(self, stats, total, t0, n_emb):
        elapsed = max(time.time() - t0, 0.01)
        done = stats["ok"] + stats["fail"]
        pct = done / max(total, 1) * 100
        fail_pct = stats["fail"] / max(done, 1) * 100
        dl_rate = done / elapsed
        emb_rate = n_emb / elapsed
        bar_w = 30
        filled = int(bar_w * done / max(total, 1))
        bar = chr(9608) * filled + chr(9617) * (bar_w - filled)
        vram = self._get_vram_info()

        return Panel(
            Text.from_markup(
                f"  [{done:,}/{total:,}] {bar} {pct:.1f}% | "
                f"OK:{stats['ok']:,} FAIL:{stats['fail']:,}({fail_pct:.0f}%) | "
                f"DL:{dl_rate:.0f}/s GPU:{emb_rate:.1f}/s | "
                f"Emb:{n_emb:,} | Batch:{self._current_batch_size}\n"
                f"  VRAM: {vram}"
            ),
            border_style="bright_green"
        )

    # ─── Hauptverarbeitung ────────────────────────────────────────────

    async def process_items(self, items: List[Dict]) -> List[Dict]:
        """Alle Items verarbeiten: Download -> GPU -> Embeddings."""
        import torch

        total = len(items)
        flush_interval = getattr(config, 'FLUSH_INTERVAL', 5.0)
        save_interval = getattr(config, 'SAVE_INTERVAL', 300.0)

        console.print(
            f"\n  Items: {total:,}  Batch: {config.BATCH_SIZE}  "
            f"Workers: {config.MAX_WORKERS}  Flush: {flush_interval}s\n"
            f"  {'CUDA FP16+TF32+Pinned' if self.device == 'cuda' else 'CPU'}\n"
            f"  336px = 576 Patches (2.25x Detail vs 224px)\n"
            f"  OOM-Recovery + Worker-Isolation + Adaptives Batching + Dynamische Batch-Groesse"
        )

        image_queue = asyncio.Queue(maxsize=config.MAX_WORKERS * 4)
        stats = {"ok": 0, "fail": 0}
        results = []
        n_emb = 0
        t0 = time.time()
        last_save = t0

        # ── Download Worker ──
        async def _worker(session, work_items):
            for item in work_items:
                url = item.get("image_url", "")
                try:
                    img = await self.download_image(session, url, item.get("source_id", ""))
                    if img is not None:
                        await image_queue.put((img, item))
                        stats["ok"] += 1
                    else:
                        stats["fail"] += 1
                except Exception:
                    stats["fail"] += 1
            await image_queue.put(_WORKER_DONE)

        n_workers = min(config.MAX_WORKERS, total)
        chunks = [[] for _ in range(n_workers)]
        for i, item in enumerate(items):
            chunks[i % n_workers].append(item)

        conn = aiohttp.TCPConnector(limit=config.MAX_WORKERS, ttl_dns_cache=300)
        pending_imgs = []
        pending_items = []

        def _flush_to_gpu():
            nonlocal n_emb
            if not pending_imgs:
                return
            batch_imgs = list(pending_imgs)
            batch_its = list(pending_items)
            pending_imgs.clear()
            pending_items.clear()
            try:
                embs = self.embed_batch_safe(batch_imgs)
                if embs is not None:
                    for j, emb in enumerate(embs):
                        r = dict(batch_its[j])
                        r["embedding"] = emb.tolist()
                        r["image_hash"] = hashlib.sha256(
                            batch_imgs[j].tobytes()[:1024]
                        ).hexdigest()[:16]
                        results.append(r)
                    n_emb += len(embs)
                    logger.debug(f"Flush: {len(embs)} embeddings (total: {n_emb})")
                else:
                    logger.warning(f"Flush gab None fuer {len(batch_imgs)} Bilder")
            except Exception as e:
                logger.error(f"GPU Flush Fehler: {e}\n{traceback.format_exc()}")

        def _save_partial():
            if not results:
                return
            try:
                save_path = Path("/app/data/cache/embedded_items_partial.json")
                with open(save_path, "w") as f:
                    json.dump(results, f)
                logger.info(f"Zwischenspeicherung: {len(results)} Embeddings")
            except Exception as e:
                logger.warning(f"Zwischenspeicherung fehlgeschlagen: {e}")

        # ═══ HAUPTSCHLEIFE ═══
        try:
            async with aiohttp.ClientSession(
                connector=conn,
                headers={"User-Agent": "ArchaeoFinder-Pipeline/4.0.0"}
            ) as session:
                with Live(
                    self._status_line(stats, total, t0, n_emb),
                    console=console, refresh_per_second=4, transient=False,
                ) as live:
                    worker_tasks = [
                        asyncio.create_task(_worker(session, chunk))
                        for chunk in chunks
                    ]
                    workers_done = 0
                    last_flush = time.time()

                    while workers_done < n_workers:
                        try:
                            result = await asyncio.wait_for(
                                image_queue.get(), timeout=1.0
                            )
                        except asyncio.TimeoutError:
                            now = time.time()
                            if now - last_flush >= flush_interval and pending_imgs:
                                _flush_to_gpu()
                                last_flush = now
                            if now - last_save >= save_interval:
                                _save_partial()
                                last_save = now
                            live.update(self._status_line(stats, total, t0, n_emb))
                            continue

                        if result is _WORKER_DONE:
                            workers_done += 1
                            continue

                        img, item = result
                        pending_imgs.append(img)
                        pending_items.append(item)

                        now = time.time()
                        if (len(pending_imgs) >= self._current_batch_size or
                                now - last_flush >= flush_interval):
                            _flush_to_gpu()
                            last_flush = now
                        if now - last_save >= save_interval:
                            _save_partial()
                            last_save = now
                        live.update(self._status_line(stats, total, t0, n_emb))

                    # Rest flushen
                    if pending_imgs:
                        _flush_to_gpu()
                    live.update(self._status_line(stats, total, t0, n_emb))

                    for t in worker_tasks:
                        try:
                            await asyncio.wait_for(t, timeout=5.0)
                        except Exception:
                            pass

        except Exception as e:
            logger.error(f"PIPELINE CRASH: {e}\n{traceback.format_exc()}")
            _save_partial()

        # ── Abschluss ──
        elapsed = time.time() - t0
        emb_rate = n_emb / max(elapsed, 0.01)
        console.print(f"\n  {n_emb:,} Embeddings ({config.CLIP_MODEL} @ {config.IMAGE_SIZE}px)")
        console.print(f"  {total:,} total, {stats['ok']:,} OK, {stats['fail']:,} failed ({stats['fail']/max(total,1)*100:.1f}%)")
        console.print(f"  {elapsed:.0f}s ({emb_rate:.1f} emb/s)")
        console.print(f"  Peak VRAM: {self._peak_vram:.2f} GB | Finale Batch: {self._current_batch_size}")
        _save_partial()
        return results