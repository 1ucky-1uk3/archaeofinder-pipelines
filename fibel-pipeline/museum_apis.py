"""
ArchaeoFinder Fibel-Pipeline v3.5.2 — Museum-API-Anbindungen (OPTIMIERT)
=========================================================================
v3.5.2 Performance-Optimierung:
  - Circuit-Breaker pro Quelle (3 Fails → Skip, spart Minuten bei toten APIs)
  - Source-Timeouts (kein einzelner Collector blockiert die Pipeline)
  - Concurrent Queries innerhalb der Quellen (Semaphore-basiert)
  - Rich Live-Progress (Echtzeit-Übersicht aller Quellen)
  - Met Museum: Query-Budget (30 Queries) + paralleler Object-Fetch
  - museum-digital: Parallele Instanzen statt sequenziell
  - Session-Timeout: 30s statt 60s, Connect: 10s

v2.2.0 Fixes (beibehalten):
  - museum-digital: Feld-Mapping (objekt_id/objekt_name), SSL-Skip, 503-Skip
  - PAS: Cloudflare-blocked → Europeana-Proxy
  - SOCH: Query-Syntax gefixt (K-samsök CQL)
  - POP: Alternativer Endpoint + Fallback
"""

import asyncio
import json
import logging
import re
import time
from typing import List, Dict, Optional
from urllib.parse import quote_plus

import aiohttp
import config
import search_terms

logger = logging.getLogger("fibel-pipeline")


# ═════════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═════════════════════════════════════════════════════════════════════════

def _first(val, default=""):
    if isinstance(val, list): return val[0] if val else default
    return val or default

def _clean_html(text):
    return re.sub(r"<[^>]+>", "", text).strip() if text else ""

def _safe(data):
    if data is None: return {}
    return data if isinstance(data, dict) else {}


# ═════════════════════════════════════════════════════════════════════════
# EU MUSEUM QUERIES (via Europeana)
# ═════════════════════════════════════════════════════════════════════════
EU_MUSEUM_QUERIES = {
    "british_museum": [
        '"British Museum" fibula', '"British Museum" brooch',
        '"British Museum" brooch Roman', '"British Museum" brooch Iron Age',
        '"British Museum" penannular brooch',
    ],
    "walters": [
        '"Walters Art" fibula', '"Walters Art" brooch',
        '"Walters Art Museum" brooch ancient',
    ],
    "penn": [
        '"Penn Museum" fibula', '"Penn Museum" brooch',
        '"University of Pennsylvania" fibula',
    ],
    "rmah_brussels": [
        '"Art and History Brussels" fibula', '"Musées royaux" fibule',
        '"Royal Museums" Brussels brooch', '"Cinquantenaire" fibule',
    ],
    "namuseet": [
        '"National Museum Denmark" fibula', '"Nationalmuseet" fibula',
        '"National Museum Denmark" brooch Viking',
    ],
    "rgzm": [
        '"RGZM" Fibel', '"LEIZA" Fibel', '"Zentralmuseum" Fibel',
        '"Römisch-Germanisches" Fibel',
    ],
    "lm_wuerttemberg": [
        '"Landesmuseum Württemberg" Fibel', '"Landesmuseum Stuttgart" Fibel',
    ],
    "gnm_nuernberg": [
        '"Germanisches Nationalmuseum" Fibel',
    ],
    "nhm_wien": [
        '"Naturhistorisches Museum Wien" Fibel',
    ],
    "khm_wien": [
        '"Kunsthistorisches Museum" Fibel', '"Kunsthistorisches Museum" fibula',
    ],
    "pas": [
        '"Portable Antiquities Scheme" brooch',
        '"Portable Antiquities" fibula',
        '"finds.org.uk" brooch',
        'brooch "Portable Antiquities" Roman',
        'brooch "Portable Antiquities" Iron Age',
        'brooch "Portable Antiquities" Medieval',
        'brooch "Portable Antiquities" Anglo-Saxon',
        '"PAS" brooch archaeological Britain',
    ],
}


# ═════════════════════════════════════════════════════════════════════════
# SOURCE TRACKER — Circuit-Breaker + Timing + Counts
# ═════════════════════════════════════════════════════════════════════════

class SourceTracker:
    """Verwaltet Circuit-Breaker, Timing und Zähler pro Quelle."""

    CIRCUIT_THRESHOLD = 3   # Consecutive fails bis Circuit öffnet
    
    def __init__(self):
        self._fails: Dict[str, int] = {}
        self._open: set = set()
        self._counts: Dict[str, int] = {}
        self._times: Dict[str, float] = {}
        self._errors: Dict[str, str] = {}
        self._start_times: Dict[str, float] = {}
    
    def start(self, source: str):
        """Markiert den Start einer Quelle."""
        self._start_times[source] = time.time()
    
    def finish(self, source: str):
        """Markiert das Ende einer Quelle."""
        if source in self._start_times:
            self._times[source] = time.time() - self._start_times[source]
    
    def ok(self, source: str) -> bool:
        """Prüft ob Quelle noch abgefragt werden soll."""
        return source not in self._open
    
    def fail(self, source: str, reason: str = ""):
        """Registriert einen Fehler. Nach CIRCUIT_THRESHOLD → Circuit öffnet."""
        self._fails[source] = self._fails.get(source, 0) + 1
        if reason:
            self._errors[source] = reason
        if self._fails[source] >= self.CIRCUIT_THRESHOLD:
            self._open.add(source)
            logger.warning(f"⚡ Circuit-Breaker OPEN: {source} (nach {self._fails[source]} Fehlern: {reason})")
    
    def fail_hard(self, source: str, reason: str = ""):
        """Sofortiger Circuit-Break (z.B. 401/403)."""
        self._open.add(source)
        self._errors[source] = reason
        logger.warning(f"⚡ Circuit-Breaker SOFORT: {source} ({reason})")
    
    def success(self, source: str):
        """Setzt Fehlerzähler zurück bei Erfolg."""
        self._fails[source] = 0
    
    def add(self, source: str, count: int = 1):
        """Zählt gesammelte Items."""
        self._counts[source] = self._counts.get(source, 0) + count
    
    def get_count(self, source: str) -> int:
        return self._counts.get(source, 0)
    
    def summary(self) -> str:
        """Gibt formatierte Zusammenfassung zurück."""
        lines = []
        total = 0
        # Sortiert nach Anzahl (absteigend)
        for src, cnt in sorted(self._counts.items(), key=lambda x: -x[1]):
            t = self._times.get(src, 0)
            status = "✅"
            if src in self._open:
                status = "⚡"
            elif cnt == 0:
                status = "⚠️"
            lines.append(f"  {status} {src:25s}  {cnt:5d} Items  ({t:5.1f}s)")
            total += cnt
        
        # Quellen die nur Fehler hatten
        for src in self._open:
            if src not in self._counts or self._counts[src] == 0:
                t = self._times.get(src, 0)
                err = self._errors.get(src, "unbekannt")
                lines.append(f"  ⚡ {src:25s}      0 Items  ({t:5.1f}s) — {err}")
        
        header = f"Phase 1 Ergebnis: {total:,} Items aus {len(self._counts)} Quellen"
        return header + "\n" + "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════
# SOURCE TIMEOUTS — Maximale Laufzeit pro Quelle
# ═════════════════════════════════════════════════════════════════════════

SOURCE_TIMEOUTS = {
    "europeana":       3000,   # 3 Min (viele Queries + Pagination)
    "met":             3000,   # 5 Min (viele Objects, aber begrenzt)
    "cleveland":        3000,   # 1 Min
    "chicago":          3000,
    "va":               3000,
    "museum_digital":  3000,   # 3 Min (16 Instanzen)
    "ddb":              3000,   # 1.5 Min
    "arachne":          3000,
    "digitalt_museum": 3000,   # 2 Min (Pagination)
    "soch":             3000,
    "pop_france":       3000,
    "eu_museums":      3000,   # 2 Min (viele kleine Museen)
    "harvard":          3000,
    "rijksmuseum":      3000,
    "smithsonian":      3000,
    "_default":         3000,
}

# Met Museum: Nur die besten Queries (statt 141 → 30)
MET_QUERY_BUDGET = 30


# ═════════════════════════════════════════════════════════════════════════
# HAUPTKLASSE
# ═════════════════════════════════════════════════════════════════════════

class MuseumCollector:
    def __init__(self):
        self.items: List[Dict] = []
        self.seen_ids = set()
        self.tracker = SourceTracker()
        # Semaphore für concurrent requests pro API
        self._sem_europeana = asyncio.Semaphore(3)   # Max 3 parallele Europeana-Queries
        self._sem_met = asyncio.Semaphore(5)          # Max 5 parallele Met-Object-Fetches
        self._sem_default = asyncio.Semaphore(3)      # Standard-APIs

    def _add(self, source, source_id, title, image_url, **kw):
        if not image_url or not source_id: return False
        key = f"{source}_{source_id}"
        if key in self.seen_ids: return False
        self.seen_ids.add(key)
        desc = kw.get("description", "")
        self.items.append({
            "source": source, "source_id": str(source_id),
            "title": (title or "Unbekannt")[:500], "image_url": image_url,
            "thumbnail_url": kw.get("thumbnail_url", ""),
            "source_url": kw.get("source_url", ""),
            "museum": kw.get("museum", ""),
            "epoch": search_terms.normalize_epoch(kw.get("epoch", "")),
            "material": search_terms.normalize_material(kw.get("material", "")),
            "region": kw.get("region", ""),
            "fibula_type": kw.get("fibula_type", "") or search_terms.detect_fibula_type(f"{title} {desc}"),
            "search_query": kw.get("search_query", ""),
            "description": (desc or "")[:2000],
        })
        self.tracker.add(source)
        return True

    async def collect_all(self) -> List[Dict]:
        """Phase 1: Alle Quellen parallel mit Timeouts und Circuit-Breaker."""
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        
        console.print(Panel(
            "[bold]Phase 1: Museum-APIs abfragen[/bold]\n"
            "Circuit-Breaker aktiv • Source-Timeouts • Concurrent Queries",
            title="🏛️ Fibel-Pipeline v3.5.2", border_style="blue"
        ))
        
        t0 = time.time()
        
        # SSL-Kontext für museum-digital
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        conn = aiohttp.TCPConnector(ssl=ssl_ctx, limit=30)

        async with aiohttp.ClientSession(
            connector=conn,
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
            headers={"User-Agent": "ArchaeoFinder-Pipeline/3.5.2 (archaeological-research)"}
        ) as session:
            # Alle Collectors als (Name, Coroutine, Timeout) Tasks
            tasks = [
                ("europeana",       self._europeana(session)),
                ("met",             self._met(session)),
                ("cleveland",       self._cleveland(session)),
                ("chicago",         self._chicago(session)),
                ("va",              self._va(session)),
                ("digitalt_museum", self._digitalt_museum(session)),
                ("museum_digital",  self._museum_digital(session)),
                ("arachne",         self._arachne(session)),
                ("soch",            self._soch(session)),
                ("pop_france",      self._pop_france(session)),
                # EU-Museen via Europeana
                ("british_museum",  self._museum_via_europeana(session, "british_museum")),
                ("walters",         self._museum_via_europeana(session, "walters")),
                ("penn",            self._museum_via_europeana(session, "penn")),
                ("pas",             self._museum_via_europeana(session, "pas")),
                ("eu_museums",      self._eu_museums(session)),
            ]
            # API-Key-abhängige Quellen
            if config.API_KEYS.get("harvard"):
                tasks.append(("harvard", self._harvard(session)))
            if config.API_KEYS.get("rijksmuseum"):
                tasks.append(("rijksmuseum", self._rijksmuseum(session)))
            if config.API_KEYS.get("smithsonian"):
                tasks.append(("smithsonian", self._smithsonian(session)))
            if config.API_KEYS.get("ddb"):
                tasks.append(("ddb", self._ddb(session)))

            # Starte alle mit individuellem Timeout
            async def _run_with_timeout(name: str, coro):
                timeout = SOURCE_TIMEOUTS.get(name, SOURCE_TIMEOUTS["_default"])
                self.tracker.start(name)
                try:
                    await asyncio.wait_for(coro, timeout=timeout)
                except asyncio.TimeoutError:
                    cnt = self.tracker.get_count(name)
                    logger.warning(f"⏱️ {name}: Timeout nach {timeout}s ({cnt} Items gesammelt)")
                except Exception as e:
                    logger.error(f"❌ {name}: {type(e).__name__}: {e}")
                finally:
                    self.tracker.finish(name)
                    cnt = self.tracker.get_count(name)
                    t = self.tracker._times.get(name, 0)
                    console.print(f"  {'✅' if cnt > 0 else '⚠️'} {name:25s} {cnt:5d} Items  ({t:.1f}s)")

            # Alle parallel starten
            await asyncio.gather(
                *[_run_with_timeout(name, coro) for name, coro in tasks],
                return_exceptions=True
            )

        # Deduplizieren
        unique = {}
        for item in self.items:
            unique.setdefault(f"{item['source']}_{item['source_id']}", item)
        self.items = list(unique.values())

        elapsed = time.time() - t0
        console.print()
        console.print(Panel(
            self.tracker.summary() + f"\n\n  ⏱️ Gesamtzeit Phase 1: {elapsed:.0f}s ({elapsed/60:.1f} Min)",
            title="📊 Phase 1 Zusammenfassung", border_style="green"
        ))
        
        return self.items

    def get_counts(self):
        return dict(sorted(self.tracker._counts.items(), key=lambda x: -x[1]))

    # ═════════════════════════════════════════════════════════════════════
    # SHARED: Europeana Query-Suche (mit Semaphore + Circuit-Breaker)
    # ═════════════════════════════════════════════════════════════════════
    async def _europeana_query(self, session, source, query, max_results=100):
        """Einzelne Europeana-Query mit Rate-Limiting via Semaphore."""
        if not self.tracker.ok(source):
            return 0
        key = config.API_KEYS.get("europeana", "")
        if not key: return 0
        count = 0
        async with self._sem_europeana:
            try:
                params = {
                    "wskey": key, "query": query,
                    "rows": min(max_results, 100), "profile": "rich", "qf": "TYPE:IMAGE"
                }
                async with session.get(
                    "https://api.europeana.eu/record/v2/search.json",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(3)
                        return 0
                    if resp.status != 200:
                        self.tracker.fail(source, f"HTTP {resp.status}")
                        return 0
                    self.tracker.success(source)
                    for item in _safe(await resp.json()).get("items", []):
                        img = _first(item.get("edmIsShownBy")) or _first(item.get("edmPreview"))
                        if img:
                            self._add(source, item.get("id", ""),
                                _first(item.get("title", "")), img,
                                thumbnail_url=_first(item.get("edmPreview", "")),
                                source_url=item.get("guid", ""),
                                museum=_first(item.get("dataProvider", "")),
                                search_query=query)
                            count += 1
                await asyncio.sleep(config.RATE_LIMITS["europeana_delay"])
            except Exception as e:
                self.tracker.fail(source, str(e)[:60])
                logger.debug(f"EU-Query '{query[:40]}': {e}")
        return count

    async def _museum_via_europeana(self, session, source_name):
        total = 0
        for q in EU_MUSEUM_QUERIES.get(source_name, []):
            if not self.tracker.ok(source_name):
                break
            total += await self._europeana_query(session, source_name, q)
        logger.info(f"{source_name} (Europeana): {total}")

    async def _eu_museums(self, session):
        total = 0
        skip = {"british_museum", "walters", "penn", "pas"}
        for name, queries in EU_MUSEUM_QUERIES.items():
            if name in skip:
                continue
            sc = 0
            for q in queries:
                if not self.tracker.ok(name):
                    break
                sc += await self._europeana_query(session, name, q)
            total += sc
            if sc > 0:
                logger.info(f"EU-Museum {name}: {sc}")
        logger.info(f"EU-Museums total: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 1) EUROPEANA — Concurrent mit Semaphore + Circuit-Breaker
    # ═════════════════════════════════════════════════════════════════════
    async def _europeana(self, session):
        key = config.API_KEYS.get("europeana", "")
        if not key: return
        rl = config.RATE_LIMITS
        total = 0
        queries = search_terms.QUERIES.get("europeana", [])

        for query in queries:
            if not self.tracker.ok("europeana"):
                break
            cursor = "*"
            qc = 0
            try:
                while cursor and qc < rl["europeana_max_per_query"]:
                    async with self._sem_europeana:
                        params = {
                            "wskey": key, "query": query,
                            "rows": rl["europeana_rows"],
                            "cursor": cursor, "profile": "rich", "qf": "TYPE:IMAGE"
                        }
                        async with session.get(
                            "https://api.europeana.eu/record/v2/search.json",
                            params=params,
                            timeout=aiohttp.ClientTimeout(total=15)
                        ) as resp:
                            if resp.status == 429:
                                await asyncio.sleep(5)
                                continue
                            if resp.status != 200:
                                self.tracker.fail("europeana", f"HTTP {resp.status}")
                                break
                            self.tracker.success("europeana")
                            data = _safe(await resp.json())
                            items = data.get("items", [])
                            if not items:
                                break
                            for item in items:
                                img = _first(item.get("edmIsShownBy")) or _first(item.get("edmPreview"))
                                if img:
                                    self._add("europeana", item.get("id", ""),
                                        _first(item.get("title", "")), img,
                                        thumbnail_url=_first(item.get("edmPreview", "")),
                                        source_url=item.get("guid", ""),
                                        museum=_first(item.get("dataProvider", "")),
                                        search_query=query)
                                    qc += 1
                                    total += 1
                            nc = data.get("nextCursor")
                            if not nc or nc == cursor:
                                break
                            cursor = nc
                        await asyncio.sleep(rl["europeana_delay"])
            except Exception as e:
                self.tracker.fail("europeana", str(e)[:60])
                logger.warning(f"Europeana '{query}': {e}")
        logger.info(f"Europeana: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 2) MET MUSEUM — Query-Budget + Concurrent Object-Fetch
    # ═════════════════════════════════════════════════════════════════════
    async def _met(self, session):
        """Met Museum: Limitiert auf MET_QUERY_BUDGET Queries,
        Object-Details parallel mit Semaphore."""
        rl = config.RATE_LIMITS
        total = 0
        queries = search_terms.QUERIES.get("met", [])[:MET_QUERY_BUDGET]
        
        hdr = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json", "Referer": "https://www.metmuseum.org/"
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20, connect=10), headers=hdr
        ) as met_session:
            for query in queries:
                if not self.tracker.ok("met"):
                    break
                try:
                    # Suche: Object-IDs holen
                    async with met_session.get(
                        "https://collectionapi.metmuseum.org/public/collection/v1/search",
                        params={"q": query, "hasImages": "true"}
                    ) as resp:
                        if resp.status == 403:
                            self.tracker.fail_hard("met", "HTTP 403 — API gesperrt")
                            return
                        if "json" not in resp.headers.get("Content-Type", ""):
                            self.tracker.fail("met", "kein JSON")
                            await asyncio.sleep(rl["met_query_delay"] * 2)
                            continue
                        data = await resp.json()
                        if not data:
                            await asyncio.sleep(rl["met_query_delay"])
                            continue
                        obj_ids = (data.get("objectIDs") or [])[:rl["met_max_per_query"]]
                    
                    self.tracker.success("met")
                    
                    # Objects: Parallel mit Semaphore (max 5 gleichzeitig)
                    async def _fetch_object(oid):
                        if not self.tracker.ok("met"):
                            return
                        async with self._sem_met:
                            try:
                                async with met_session.get(
                                    f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}"
                                ) as r2:
                                    if r2.status == 403:
                                        self.tracker.fail("met", "Object 403")
                                        return
                                    if "json" not in r2.headers.get("Content-Type", ""):
                                        return
                                    obj = await r2.json()
                                    if not obj or not obj.get("primaryImage"):
                                        return
                                    self._add("met", str(oid), obj.get("title", ""),
                                        obj["primaryImage"],
                                        thumbnail_url=obj.get("primaryImageSmall", ""),
                                        source_url=obj.get("objectURL", ""),
                                        museum="Metropolitan Museum of Art",
                                        epoch=obj.get("objectDate", ""),
                                        material=obj.get("medium", ""),
                                        region=obj.get("culture", ""),
                                        search_query=query)
                                await asyncio.sleep(rl["met_object_delay"])
                            except Exception:
                                pass
                    
                    # Parallel fetch alle Objects dieser Query
                    await asyncio.gather(*[_fetch_object(oid) for oid in obj_ids])
                    await asyncio.sleep(rl["met_query_delay"])
                    
                except Exception as e:
                    self.tracker.fail("met", str(e)[:60])
                    logger.warning(f"Met '{query}': {e}")
                    await asyncio.sleep(rl["met_query_delay"])
        
        total = self.tracker.get_count("met")
        logger.info(f"Met Museum: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 3-5) CLEVELAND, CHICAGO, V&A — mit Circuit-Breaker
    # ═════════════════════════════════════════════════════════════════════
    async def _cleveland(self, session):
        total = 0
        for q in search_terms.QUERIES.get("cleveland", []):
            if not self.tracker.ok("cleveland"):
                break
            try:
                async with self._sem_default:
                    async with session.get(
                        "https://openaccess-api.clevelandart.org/api/artworks/",
                        params={"q": q, "has_image": 1, "limit": 50}
                    ) as resp:
                        if resp.status != 200:
                            self.tracker.fail("cleveland", f"HTTP {resp.status}")
                            continue
                        self.tracker.success("cleveland")
                        for item in _safe(await resp.json()).get("data", []):
                            img = (item.get("images") or {}).get("web", {}).get("url")
                            if img:
                                self._add("cleveland", str(item.get("id", "")),
                                    item.get("title", ""), img,
                                    source_url=item.get("url", ""),
                                    museum="Cleveland Museum of Art",
                                    epoch=item.get("creation_date", ""),
                                    material=item.get("technique", ""),
                                    search_query=q)
                                total += 1
                await asyncio.sleep(config.RATE_LIMITS["default_delay"])
            except Exception as e:
                self.tracker.fail("cleveland", str(e)[:60])
                logger.warning(f"Cleveland '{q}': {e}")
        logger.info(f"Cleveland: {total}")

    async def _chicago(self, session):
        total = 0
        for q in search_terms.QUERIES.get("chicago", []):
            if not self.tracker.ok("chicago"):
                break
            try:
                async with self._sem_default:
                    async with session.get(
                        "https://api.artic.edu/api/v1/artworks/search",
                        params={"q": q, "limit": 50,
                                "fields": "id,title,image_id,date_display,medium_display",
                                "query[term][is_public_domain]": "true"}
                    ) as resp:
                        if resp.status != 200:
                            self.tracker.fail("chicago", f"HTTP {resp.status}")
                            continue
                        self.tracker.success("chicago")
                        data = _safe(await resp.json())
                        iiif = data.get("config", {}).get("iiif_url", "https://www.artic.edu/iiif/2")
                        for item in data.get("data", []):
                            iid = item.get("image_id", "")
                            if iid:
                                self._add("chicago", str(item.get("id", "")),
                                    item.get("title", ""),
                                    f"{iiif}/{iid}/full/843,/0/default.jpg",
                                    thumbnail_url=f"{iiif}/{iid}/full/200,/0/default.jpg",
                                    source_url=f"https://www.artic.edu/artworks/{item.get('id', '')}",
                                    museum="Art Institute of Chicago",
                                    epoch=item.get("date_display", ""),
                                    material=item.get("medium_display", ""),
                                    search_query=q)
                                total += 1
                await asyncio.sleep(config.RATE_LIMITS["default_delay"])
            except Exception as e:
                self.tracker.fail("chicago", str(e)[:60])
                logger.warning(f"Chicago '{q}': {e}")
        logger.info(f"Chicago: {total}")

    async def _va(self, session):
        total = 0
        for q in search_terms.QUERIES.get("va", []):
            if not self.tracker.ok("va"):
                break
            try:
                async with self._sem_default:
                    async with session.get(
                        "https://api.vam.ac.uk/v2/objects/search",
                        params={"q": q, "page_size": 50, "images_exist": 1}
                    ) as resp:
                        if resp.status != 200:
                            self.tracker.fail("va", f"HTTP {resp.status}")
                            continue
                        self.tracker.success("va")
                        for item in _safe(await resp.json()).get("records", []):
                            img = item.get("_images", {}).get("_primary_thumbnail")
                            if img:
                                self._add("va", item.get("systemNumber", ""),
                                    item.get("_primaryTitle", ""), img,
                                    source_url=f"https://collections.vam.ac.uk/item/{item.get('systemNumber', '')}",
                                    museum="Victoria & Albert Museum",
                                    epoch=item.get("_primaryDate", ""),
                                    search_query=q)
                                total += 1
                await asyncio.sleep(config.RATE_LIMITS["default_delay"])
            except Exception as e:
                self.tracker.fail("va", str(e)[:60])
                logger.warning(f"V&A '{q}': {e}")
        logger.info(f"V&A: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 6-8) HARVARD, RIJKSMUSEUM, SMITHSONIAN (Key-basiert)
    # ═════════════════════════════════════════════════════════════════════
    async def _harvard(self, session):
        total = 0
        key = config.API_KEYS["harvard"]
        for q in search_terms.QUERIES.get("harvard", []):
            if not self.tracker.ok("harvard"):
                break
            try:
                async with self._sem_default:
                    async with session.get(
                        "https://api.harvardartmuseums.org/object",
                        params={"apikey": key, "q": q, "size": 50, "hasimage": 1}
                    ) as resp:
                        if resp.status in (401, 403):
                            self.tracker.fail_hard("harvard", f"HTTP {resp.status}")
                            return
                        if resp.status != 200:
                            self.tracker.fail("harvard", f"HTTP {resp.status}")
                            continue
                        self.tracker.success("harvard")
                        for item in _safe(await resp.json()).get("records", []):
                            if item.get("primaryimageurl"):
                                self._add("harvard", str(item.get("id", "")),
                                    item.get("title", ""), item["primaryimageurl"],
                                    source_url=item.get("url", ""),
                                    museum="Harvard Art Museums",
                                    epoch=item.get("dated", ""),
                                    material=item.get("medium", ""),
                                    search_query=q)
                                total += 1
                await asyncio.sleep(config.RATE_LIMITS["default_delay"])
            except Exception as e:
                self.tracker.fail("harvard", str(e)[:60])
                logger.warning(f"Harvard '{q}': {e}")
        logger.info(f"Harvard: {total}")

    async def _rijksmuseum(self, session):
        total = 0
        key = config.API_KEYS["rijksmuseum"]
        for q in search_terms.QUERIES.get("rijksmuseum", []):
            if not self.tracker.ok("rijksmuseum"):
                break
            try:
                async with self._sem_default:
                    async with session.get(
                        "https://www.rijksmuseum.nl/api/en/collection",
                        params={"key": key, "q": q, "ps": 50, "imgonly": "true", "format": "json"}
                    ) as resp:
                        if resp.status in (401, 403):
                            self.tracker.fail_hard("rijksmuseum", f"HTTP {resp.status}")
                            return
                        if resp.status != 200:
                            self.tracker.fail("rijksmuseum", f"HTTP {resp.status}")
                            continue
                        self.tracker.success("rijksmuseum")
                        for item in _safe(await resp.json()).get("artObjects", []):
                            img = item.get("webImage", {}).get("url", "")
                            if img:
                                self._add("rijksmuseum", item.get("objectNumber", ""),
                                    item.get("title", ""), img,
                                    source_url=item.get("links", {}).get("web", ""),
                                    museum="Rijksmuseum Amsterdam",
                                    search_query=q)
                                total += 1
                await asyncio.sleep(config.RATE_LIMITS["default_delay"])
            except Exception as e:
                self.tracker.fail("rijksmuseum", str(e)[:60])
                logger.warning(f"Rijksmuseum '{q}': {e}")
        logger.info(f"Rijksmuseum: {total}")

    async def _smithsonian(self, session):
        total = 0
        key = config.API_KEYS["smithsonian"]
        for q in search_terms.QUERIES.get("smithsonian", []):
            if not self.tracker.ok("smithsonian"):
                break
            try:
                async with self._sem_default:
                    async with session.get(
                        "https://api.si.edu/openaccess/api/v1.0/search",
                        params={"api_key": key, "q": q + " AND online_media_type:Images", "rows": 50}
                    ) as resp:
                        if resp.status in (401, 403):
                            self.tracker.fail_hard("smithsonian", f"HTTP {resp.status}")
                            return
                        if resp.status != 200:
                            self.tracker.fail("smithsonian", f"HTTP {resp.status}")
                            continue
                        self.tracker.success("smithsonian")
                        for row in _safe(await resp.json()).get("response", {}).get("rows", []):
                            c = row.get("content", {})
                            d = c.get("descriptiveNonRepeating", {})
                            media = c.get("online_media", {}).get("media", [])
                            img = media[0].get("content", "") if media else ""
                            if img:
                                self._add("smithsonian", row.get("id", ""),
                                    d.get("title", {}).get("content", ""), img,
                                    source_url=d.get("record_link", ""),
                                    museum=d.get("unit_name", "Smithsonian"),
                                    search_query=q)
                                total += 1
                await asyncio.sleep(config.RATE_LIMITS["default_delay"])
            except Exception as e:
                self.tracker.fail("smithsonian", str(e)[:60])
                logger.warning(f"Smithsonian '{q}': {e}")
        logger.info(f"Smithsonian: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 9) DDB — mit Circuit-Breaker
    # ═════════════════════════════════════════════════════════════════════
    async def _ddb(self, session):
        total = 0
        key = config.API_KEYS.get("ddb", "")
        if not key: return
        rl = config.RATE_LIMITS
        base = "https://api.deutsche-digitale-bibliothek.de"
        
        for query in search_terms.QUERIES.get("ddb", []):
            if not self.tracker.ok("ddb"):
                break
            try:
                offset = 0
                while offset < rl["ddb_max_per_query"]:
                    params = {
                        "query": query, "rows": rl["ddb_rows"],
                        "offset": offset, "oauth_consumer_key": key
                    }
                    async with session.get(f"{base}/search", params=params) as resp:
                        if resp.status in (401, 403):
                            self.tracker.fail_hard("ddb", f"HTTP {resp.status}")
                            return
                        if resp.status != 200:
                            self.tracker.fail("ddb", f"HTTP {resp.status}")
                            break
                        self.tracker.success("ddb")
                        data = _safe(await resp.json())
                        nf = data.get("numberOfResults", 0)
                        docs = []
                        for g in data.get("results", []):
                            if isinstance(g, dict):
                                docs.extend(g.get("docs", []))
                        if not docs:
                            break
                        for doc in docs:
                            if not isinstance(doc, dict): continue
                            iid = doc.get("id", "")
                            if not iid or (doc.get("media") and doc["media"] != "image"):
                                continue
                            title = _clean_html(doc.get("label", "") or doc.get("title", ""))
                            img = self._ddb_img(doc, key)
                            if not title or not img: continue
                            self._add("ddb", iid, title, img,
                                source_url=f"https://www.deutsche-digitale-bibliothek.de/item/{iid}",
                                museum=_clean_html(doc.get("subtitle", "")),
                                search_query=query)
                            total += 1
                        offset += rl["ddb_rows"]
                        try:
                            if offset >= int(nf): break
                        except: break
                    await asyncio.sleep(rl["default_delay"])
            except Exception as e:
                self.tracker.fail("ddb", str(e)[:60])
                logger.warning(f"DDB '{query}': {e}")
        logger.info(f"DDB: {total}")

    @staticmethod
    def _ddb_img(doc, api_key):
        t = doc.get("thumbnail", "")
        if isinstance(t, str) and t.startswith("http"): return t
        p = doc.get("preview", "")
        if isinstance(p, str):
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', p)
            if m:
                s = m.group(1)
                if s.startswith("http"):
                    return s.replace("!200,200", "!800,800").replace("!400,400", "!800,800") if "iiif" in s else s
                if len(s) > 8:
                    return f"https://iiif.deutsche-digitale-bibliothek.de/image/2/{s}/full/!800,800/0/default.jpg"
        iid = doc.get("id", "")
        return f"https://api.deutsche-digitale-bibliothek.de/binary/{iid}/mvpr/1.jpg?oauth_consumer_key={api_key}" if iid else ""

    # ═════════════════════════════════════════════════════════════════════
    # 10) MUSEUM-DIGITAL — Parallele Instanzen + Circuit-Breaker
    # ═════════════════════════════════════════════════════════════════════
    async def _museum_digital(self, session):
        """museum-digital.de: Instanzen parallel, Circuit-Breaker pro Instanz."""
        queries = search_terms.QUERIES.get("museum_digital", [])
        mx = config.MUSEUM_DIGITAL_MAX_PER_INSTANCE
        
        sem = asyncio.Semaphore(4)  # Max 4 Instanzen parallel

        async def _collect_instance(inst):
            nm = inst.split("//")[1].split(".")[0]
            ic = 0
            inst_failed = False

            for q in queries:
                if ic >= mx or inst_failed:
                    break
                if not self.tracker.ok("museum_digital"):
                    break

                data = None
                async with sem:
                    try:
                        async with session.get(
                            f"{inst}/json/objects",
                            params={"s": q, "output": "json", "limit": 50},
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp:
                            if resp.status == 503:
                                if not inst_failed:
                                    logger.info(f"museum-digital {nm}: 503 — skip")
                                    inst_failed = True
                                break
                            if resp.status != 200:
                                continue
                            try:
                                data = await resp.json(content_type=None)
                            except Exception:
                                raw = await resp.text()
                                if raw.strip().startswith(("{", "[")):
                                    data = json.loads(raw)
                    except (aiohttp.ClientConnectorCertificateError, aiohttp.ClientConnectorSSLError):
                        if not inst_failed:
                            logger.info(f"museum-digital {nm}: SSL-Fehler — skip")
                            inst_failed = True
                        break
                    except Exception as e:
                        if not inst_failed:
                            logger.debug(f"museum-digital {nm}: {type(e).__name__}: {e}")
                            inst_failed = True
                        break

                if not data:
                    continue

                items = data if isinstance(data, list) else data.get("objects", data.get("results", []))
                for item in (items or []):
                    if not isinstance(item, dict) or ic >= mx:
                        break

                    oid = str(item.get("objekt_id", item.get("object_id", item.get("id", ""))))
                    if not oid: continue
                    title = item.get("objekt_name", item.get("object_name", item.get("title", item.get("name", ""))))
                    if not title: continue
                    img = self._md_img(item, inst, oid)
                    if not img: continue

                    museum_name = item.get("institution_name",
                        item.get("institution", item.get("museum", item.get("sammlung", f"museum-digital ({nm})"))))

                    self._add("museum_digital", f"md_{nm}_{oid}", title, img,
                        source_url=item.get("objekt_url", item.get("url", f"{inst}/?t=objekt&oession={oid}")),
                        museum=museum_name,
                        epoch=item.get("datierung", item.get("dating", item.get("period", ""))),
                        material=item.get("material", ""),
                        region=item.get("ort", item.get("place", item.get("findspot", ""))),
                        search_query=q,
                        description=(item.get("objekt_beschreibung", item.get("description", "")) or "")[:300])
                    ic += 1

                await asyncio.sleep(config.RATE_LIMITS["slow_delay"])

            if ic > 0:
                logger.info(f"museum-digital {nm}: {ic}")
            return ic

        # Alle Instanzen parallel
        results = await asyncio.gather(
            *[_collect_instance(inst) for inst in config.MUSEUM_DIGITAL_INSTANCES],
            return_exceptions=True
        )
        total = sum(r for r in results if isinstance(r, int))
        logger.info(f"museum-digital total: {total}")

    @staticmethod
    def _md_img(item, base_url, oid):
        for field in ("objekt_bild", "image", "images", "bild"):
            val = item.get(field)
            if isinstance(val, str) and val:
                return val if val.startswith("http") else f"{base_url}/{val}"
            if isinstance(val, list) and val:
                first = val[0]
                if isinstance(first, str):
                    return first if first.startswith("http") else f"{base_url}/{first}"
                if isinstance(first, dict):
                    url = first.get("url", first.get("src", first.get("pfad", "")))
                    if url:
                        return url if url.startswith("http") else f"{base_url}/{url}"
            if isinstance(val, dict):
                url = val.get("url", val.get("src", val.get("pfad", "")))
                if url:
                    return url if url.startswith("http") else f"{base_url}/{url}"
        if oid:
            return f"{base_url}/data/json/images/objects/{oid}/1.jpg"
        return ""

    # ═════════════════════════════════════════════════════════════════════
    # 11) DIGITALTMUSEUM
    # ═════════════════════════════════════════════════════════════════════
    async def _digitalt_museum(self, session):
        total = 0
        for query in search_terms.QUERIES.get("digitalt_museum", []):
            if not self.tracker.ok("digitalt_museum"):
                break
            for page in range(config.DIMU_MAX_PAGES):
                try:
                    params = {
                        "q": query, "wt": "json", "rows": config.DIMU_MAX_ROWS,
                        "start": page * config.DIMU_MAX_ROWS,
                        "fq": "artifact.hasPictures:true", "api.key": config.DIMU_API_KEY
                    }
                    async with session.get(
                        config.DIMU_API_URL, params=params,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status != 200:
                            self.tracker.fail("digitalt_museum", f"HTTP {resp.status}")
                            break
                        self.tracker.success("digitalt_museum")
                        try:
                            data = await resp.json(content_type=None)
                        except:
                            raw = await resp.text()
                            data = json.loads(raw) if raw.strip().startswith("{") else {}
                        response = data.get("response", {})
                        docs = response.get("docs", [])
                        if not docs: break
                        for doc in docs:
                            if not isinstance(doc, dict): continue
                            did = doc.get("identifier.id", doc.get("id", ""))
                            if not did: continue
                            mid = doc.get("artifact.defaultMediaIdentifier", "")
                            img = f"https://digitaltmuseum.org/media/{mid}/image" if mid else doc.get("artifact.defaultPictureURL", "")
                            if not img: continue
                            title = doc.get("artifact.name", doc.get("artifact.defaultTitle", query))
                            museum = _first(doc.get("artifact.owner", ""))
                            epoch = _first(doc.get("artifact.eventDate", doc.get("artifact.date", "")))
                            mat = doc.get("artifact.material", "")
                            if isinstance(mat, list): mat = ", ".join(mat[:3])
                            self._add("digitalt_museum", str(did), title, img,
                                source_url=f"https://digitaltmuseum.org/{did}",
                                museum=museum if isinstance(museum, str) else "",
                                epoch=epoch if isinstance(epoch, str) else "",
                                material=mat if isinstance(mat, str) else "",
                                search_query=query)
                            total += 1
                        if (page + 1) * config.DIMU_MAX_ROWS >= response.get("numFound", 0):
                            break
                    await asyncio.sleep(config.RATE_LIMITS["slow_delay"])
                except Exception as e:
                    self.tracker.fail("digitalt_museum", str(e)[:60])
                    logger.debug(f"DiMu '{query}' p{page}: {e}")
                    break
        logger.info(f"DigitaltMuseum: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 12) ARACHNE
    # ═════════════════════════════════════════════════════════════════════
    async def _arachne(self, session):
        total = 0
        arachne_queries = [
            "fibula", "Fibel", "brooch", "Buegelfibel", "Scheibenfibel",
            "Armbrustfibel", "fibula roman", "crossbow brooch"
        ]
        for q in arachne_queries:
            if not self.tracker.ok("arachne"):
                break
            try:
                async with session.get(
                    "https://arachne.dainst.org/data/search",
                    params={"q": q, "fq": "facet_image:ja", "limit": 100, "offset": 0},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        self.tracker.fail("arachne", f"HTTP {resp.status}")
                        continue
                    self.tracker.success("arachne")
                    for ent in _safe(await resp.json()).get("entities", []):
                        if not isinstance(ent, dict): continue
                        eid = str(ent.get("entityId", ""))
                        tid = ent.get("thumbnailId", "")
                        title = ent.get("title", ent.get("subtitle", ""))
                        if not eid or not tid or not title: continue
                        self._add("arachne", f"arachne_{eid}", title,
                            f"https://arachne.dainst.org/data/image/{tid}",
                            thumbnail_url=f"https://arachne.dainst.org/data/image/width/200/{tid}",
                            source_url=f"https://arachne.dainst.org/entity/{eid}",
                            museum="ARACHNE / DAI",
                            epoch=ent.get("subtitle", ""),
                            search_query=q)
                        total += 1
                await asyncio.sleep(config.RATE_LIMITS["slow_delay"])
            except Exception as e:
                self.tracker.fail("arachne", str(e)[:60])
                logger.debug(f"ARACHNE '{q}': {e}")
        logger.info(f"ARACHNE: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 13) SOCH (K-samsök)
    # ═════════════════════════════════════════════════════════════════════
    async def _soch(self, session):
        total = 0
        soch_queries = ["fibula", "brosch", "spänne", "dräktspänne", "ringspänne"]
        for q in soch_queries:
            if not self.tracker.ok("soch"):
                break
            try:
                params = {
                    "method": "search", "hitsPerPage": 250, "startRecord": 1,
                    "query": f"text={q}", "x-api": "archaeofinder",
                }
                async with session.get(
                    "https://www.kulturarvsdata.se/ksamsok/api",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    if resp.status != 200:
                        self.tracker.fail("soch", f"HTTP {resp.status}")
                        continue
                    self.tracker.success("soch")
                    body = await resp.text()
                    if q == "fibula":
                        logger.info(f"SOCH '{q}': {len(body)} bytes, hits={body.count('<record')}")
                    records = re.findall(r'<record>(.*?)</record>', body, re.DOTALL)
                    for rec in records:
                        rid_m = re.search(r'<pres:id[^>]*>([^<]+)</pres:id>', rec)
                        if not rid_m:
                            rid_m = re.search(r'rdf:about="([^"]+)"', rec)
                        if not rid_m: continue
                        rid = rid_m.group(1)
                        img = ""
                        for pattern in [r'<pres:image[^>]*>([^<]+)</pres:image>',
                                        r'<pres:imageUrl[^>]*>([^<]+)</pres:imageUrl>',
                                        r'<image[^>]*>([^<]+)</image>']:
                            img_m = re.search(pattern, rec)
                            if img_m:
                                img = img_m.group(1)
                                break
                        if not img: continue
                        title = ""
                        t_m = re.search(r'<pres:itemLabel[^>]*>([^<]+)</pres:itemLabel>', rec)
                        if t_m:
                            title = t_m.group(1)
                        if not title:
                            t_m = re.search(r'<pres:description[^>]*>([^<]+)</pres:description>', rec)
                            if t_m: title = t_m.group(1)[:100]
                        if not title: title = q
                        museum = ""
                        o_m = re.search(r'<pres:organization[^>]*>([^<]+)</pres:organization>', rec)
                        if o_m: museum = o_m.group(1)
                        url = ""
                        u_m = re.search(r'<pres:url[^>]*>([^<]+)</pres:url>', rec)
                        if u_m: url = u_m.group(1)
                        if not url: url = f"https://www.kulturarvsdata.se/{rid}"
                        self._add("soch", f"soch_{rid.replace('/', '_')}", title, img,
                            source_url=url, museum=museum or "SOCH Sweden", search_query=q)
                        total += 1
                await asyncio.sleep(config.RATE_LIMITS["slow_delay"])
            except Exception as e:
                self.tracker.fail("soch", str(e)[:60])
                logger.warning(f"SOCH '{q}': {e}")
        logger.info(f"SOCH: {total}")

    # ═════════════════════════════════════════════════════════════════════
    # 14) POP/JOCONDE — mit Circuit-Breaker
    # ═════════════════════════════════════════════════════════════════════
    async def _pop_france(self, session):
        total = 0
        pop_queries = ["fibule", "broche romaine", "fibule romaine",
                       "fibule bronze", "agrafe antique"]
        endpoints = [
            "https://api.pop.culture.gouv.fr/search/joconde",
            "https://api.pop.culture.gouv.fr/search/museo",
            "https://api.pop.culture.gouv.fr/search/palissy",
        ]
        working_endpoint = None

        for ep in endpoints:
            try:
                test_payload = {
                    "query": {"bool": {"must": [
                        {"multi_match": {"query": "fibule", "fields": ["TITR", "DENO", "DESC"]}},
                    ]}},
                    "size": 1, "from": 0,
                }
                async with session.post(ep, json=test_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    logger.info(f"POP endpoint {ep.split('/')[-1]}: HTTP {resp.status}")
                    if resp.status == 200:
                        working_endpoint = ep
                        self.tracker.success("pop_france")
                        break
            except Exception as e:
                logger.debug(f"POP {ep}: {e}")

        if working_endpoint:
            for q in pop_queries:
                if not self.tracker.ok("pop_france"):
                    break
                try:
                    payload = {
                        "query": {"bool": {"must": [
                            {"multi_match": {"query": q, "fields": ["TITR", "DENO", "DESC"]}},
                            {"exists": {"field": "IMG"}}
                        ]}},
                        "size": 100, "from": 0,
                        "_source": ["REF", "TITR", "DENO", "IMG", "EPOQ", "TECH", "LOCA", "MUSEO"]
                    }
                    async with session.post(working_endpoint, json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status != 200:
                            self.tracker.fail("pop_france", f"HTTP {resp.status}")
                            continue
                        self.tracker.success("pop_france")
                        data = _safe(await resp.json())
                        for hit in data.get("hits", {}).get("hits", []):
                            src = hit.get("_source", {})
                            ref = src.get("REF", "")
                            if not ref: continue
                            imgs = src.get("IMG", [])
                            if not imgs: continue
                            img_f = imgs[0] if isinstance(imgs, list) else imgs
                            if not isinstance(img_f, str) or not img_f: continue
                            img_url = img_f if img_f.startswith("http") else f"https://pop-images.culture.gouv.fr/{ref}/{img_f}"
                            title = _first(src.get("TITR", src.get("DENO", "")))
                            if not title: continue
                            self._add("pop_france", f"pop_{ref}", title, img_url,
                                source_url=f"https://www.pop.culture.gouv.fr/notice/joconde/{ref}",
                                museum=src.get("LOCA", src.get("MUSEO", "France")),
                                epoch=_first(src.get("EPOQ", "")),
                                material=_first(src.get("TECH", "")),
                                search_query=q)
                            total += 1
                    await asyncio.sleep(config.RATE_LIMITS["slow_delay"])
                except Exception as e:
                    self.tracker.fail("pop_france", str(e)[:60])
                    logger.debug(f"POP '{q}': {e}")
        else:
            # Fallback: Französische Museen via Europeana
            logger.info("POP: Kein Endpoint funktioniert — Europeana-Fallback")
            for q in ['"fibule" musée France', '"broche romaine" France',
                      '"fibule" Louvre', '"fibule" museum French']:
                total += await self._europeana_query(session, "pop_france", q)

        logger.info(f"POP France: {total}")
