"""
ArchaeoFinder Fibel-Pipeline v3.0.0 — Neue Quellen
====================================================
Wird von museum_apis.py importiert und erweitert MuseumCollector.

Neue Quellen:
 - Badisches Landesmuseum (katalog.landesmuseum.de)
 - DigiCult Saarland (saarland.digicult-museen.net)
 - CoinHirsch Auktionen (coinhirsch.bidinside.com)
 - Kelten-Roemer Museen (via Europeana)
 - 15+ weitere dt./europ. Landesmuseen (via Europeana)
"""

import asyncio
import logging
import re
from typing import List, Dict
from urllib.parse import quote_plus

import aiohttp
import config
import search_terms

logger = logging.getLogger("fibel-pipeline")


# =============================================================================
# EUROPEANA PROVIDER-QUERIES: Gezielte Museen
# =============================================================================
# Diese Queries finden Fibeln spezifischer Museen ueber Europeana.

EU_MUSEUM_QUERIES_NEW = {
    # ─── Badisches Landesmuseum ───
    "blm_karlsruhe": [
        '"Badisches Landesmuseum" Fibel',
        '"Badisches Landesmuseum" Brosche',
        '"Badisches Landesmuseum" Gewandnadel',
        '"Badisches Landesmuseum" Bronze roemisch',
        '"Badisches Landesmuseum" keltisch Latene',
        '"Badisches Landesmuseum" Schmuck antik',
    ],
    # ─── Kelten-Roemer Museen ───
    "kelten_roemer": [
        '"Kelten" Fibel Bronze museum',
        '"Roemer" Fibel museum Bronze',
        'keltisch roemisch Fibel Museum',
        '"kelten-roemer" Fibel',
        '"Roemermuseum" Fibel Bronze',
        '"Limesmuseum" Fibel Aalen',
        '"Saalburgmuseum" Fibel',
        '"Museum Kalkriese" Fibel',
        '"Roemermuseum Xanten" Fibel',
        '"Roemermuseum Haltern" Fibel',
    ],
    # ─── DigiCult Saarland ───
    "digicult_saarland": [
        '"Saarland" Fibel museum',
        '"Historisches Museum Saar" Fibel',
        '"Museum Saarland" roemisch Bronze',
        '"saarlaendisch" Fibel Gewandnadel',
        '"Saarbruecken" Fibel museum archaeologie',
    ],
    # ─── Landesmuseum Wuerttemberg Stuttgart ───
    "lm_wuerttemberg_extra": [
        '"Landesmuseum Württemberg" Fibel Bronze',
        '"Landesmuseum Württemberg" Brosche',
        '"Landesmuseum Stuttgart" Gewandnadel',
        '"Württembergisches Landesmuseum" Bronze Latene',
    ],
    # ─── LVR-LandesMuseum Bonn ───
    "rlm_bonn": [
        '"LandesMuseum Bonn" Fibel',
        '"LVR" Fibel roemisch',
        '"Rheinisches Landesmuseum Bonn" Fibel',
        '"LVR-LandesMuseum" Brosche Bronze',
    ],
    # ─── Rheinisches Landesmuseum Trier ───
    "rlm_trier": [
        '"Landesmuseum Trier" Fibel',
        '"Rheinisches Landesmuseum Trier" Fibel Bronze',
        '"Trier" roemisch Fibel museum',
    ],
    # ─── Landesmuseum Halle (Vorgeschichte) ───
    "lda_halle": [
        '"Landesmuseum" "Vorgeschichte" Fibel',
        '"Landesmuseum Halle" Fibel Bronze',
        '"Halle" archaeologie Fibel',
    ],
    # ─── Historisches Museum der Pfalz Speyer ───
    "museum_speyer": [
        '"Museum der Pfalz" Fibel',
        '"Speyer" Fibel roemisch museum',
        '"Historisches Museum der Pfalz" Bronze',
    ],
    # ─── Archaeologische Staatssammlung Muenchen ───
    "arch_staatssammlung": [
        '"Archaeologische Staatssammlung" Fibel',
        '"Staatssammlung" Muenchen Fibel Bronze',
        '"AMSM" Fibel',
    ],
    # ─── Landesmuseum Mainz ───
    "lm_mainz": [
        '"Landesmuseum Mainz" Fibel',
        '"GDKE" Fibel Mainz',
        '"Mainz" Fibel roemisch museum',
    ],
    # ─── Germanisches Nationalmuseum Nuernberg ───
    "gnm_extra": [
        '"Germanisches Nationalmuseum" Fibel Bronze',
        '"Germanisches Nationalmuseum" Gewandnadel',
        '"GNM" Fibel mittelalterlich',
    ],
    # ─── Landesmuseum Hannover ───
    "lm_hannover": [
        '"Landesmuseum Hannover" Fibel',
        '"Niedersaechsisches Landesmuseum" Fibel',
    ],
    # ─── LWL Museum Herne ───
    "lwl_herne": [
        '"LWL-Museum" Fibel',
        '"LWL" archaeologie Fibel Westfalen',
        '"Herne" archaeologie Fibel museum',
    ],
    # ─── Pfahlbaumuseum Unteruhldingen ───
    "pfahlbaumuseum": [
        '"Pfahlbaumuseum" Fibel',
        '"Unteruhldingen" Fibel Bronze',
    ],
    # ─── Oesterreich ───
    "at_museen": [
        '"Naturhistorisches Museum Wien" Fibel',
        '"Kunsthistorisches Museum" Fibel',
        '"Salzburg Museum" Fibel',
        '"Universalmuseum Joanneum" Fibel',
        '"Oberoesterreichisches Landesmuseum" Fibel',
        '"Carnuntum" Fibel',
    ],
    # ─── Schweiz ───
    "ch_museen": [
        '"Schweizerisches Nationalmuseum" Fibel',
        '"Landesmuseum Zuerich" Fibel',
        '"Vindonissa" Fibel',
        '"Augusta Raurica" Fibel',
        '"Bern" Fibel museum archaeologie',
    ],
    # ─── Niederlande / Belgien ───
    "nl_be_museen": [
        '"Rijksmuseum van Oudheden" fibula',
        '"Allard Pierson" fibula',
        '"Gallo-Romeins Museum" fibula Tongeren',
        '"Musees royaux" fibule Brussels',
    ],
    # ─── Italien ───
    "it_museen": [
        '"Museo Nazionale Romano" fibula',
        '"Museo Archeologico Nazionale" fibula',
        '"Museo Nazionale Etrusco" fibula',
        '"Bologna" fibula museo',
        '"Aquileia" fibula museo',
    ],
    # ─── Archaeologisches Museum Frankfurt ───
    "arch_frankfurt": [
        '"Archaeologisches Museum Frankfurt" Fibel',
        '"AMF" Fibel Bronze Frankfurt',
    ],
}


# =============================================================================
# HTML SCRAPER: Badisches Landesmuseum Karlsruhe
# =============================================================================

async def scrape_badisches_lm(session, collector):
    """Scrape katalog.landesmuseum.de fuer Fibeln/Broschen."""
    total = 0
    queries = search_terms.QUERIES.get("badisches_lm", [])
    base = "https://katalog.landesmuseum.de"

    for query in queries:
        try:
            url = f"{base}/search?term={quote_plus(query)}&type=Object"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    logger.debug(f"Badisches LM '{query}': HTTP {resp.status}")
                    continue
                html = await resp.text()

            # Objektlinks extrahieren
            links = re.findall(r'href="(/object/[^"]+)"', html)
            links = list(set(links))[:20]  # Max 20 pro Query

            for link in links:
                try:
                    obj_url = f"{base}{link}"
                    async with session.get(obj_url, timeout=aiohttp.ClientTimeout(total=10)) as r2:
                        if r2.status != 200:
                            continue
                        obj_html = await r2.text()

                    # Titel
                    title_m = re.search(r'<h1[^>]*>([^<]+)</h1>', obj_html)
                    title = title_m.group(1).strip() if title_m else ""
                    if not title:
                        title_m = re.search(r'<title>([^<]+)</title>', obj_html)
                        title = title_m.group(1).strip() if title_m else query

                    # Bild
                    img = ""
                    img_patterns = [
                        r'<img[^>]+class="[^"]*object-image[^"]*"[^>]+src="([^"]+)"',
                        r'<img[^>]+src="(https://[^"]*iiif[^"]*)"',
                        r'<img[^>]+src="(https://katalog\.landesmuseum\.de/[^"]*\.(?:jpg|jpeg|png))"',
                        r'"(https://[^"]+/iiif/[^"]+/full/[^"]+)"',
                        r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
                    ]
                    for pat in img_patterns:
                        img_m = re.search(pat, obj_html, re.IGNORECASE)
                        if img_m:
                            img = img_m.group(1)
                            break

                    if not img or not title:
                        continue

                    # Objekt-ID
                    oid_m = re.search(r'/object/([^/"]+)', link)
                    oid = oid_m.group(1) if oid_m else link.replace("/", "_")

                    # Epoche
                    epoch = ""
                    ep_m = re.search(r'Datierung[^<]*</[^>]+>\s*<[^>]+>([^<]+)', obj_html)
                    if ep_m:
                        epoch = ep_m.group(1).strip()

                    # Material
                    material = ""
                    mat_m = re.search(r'Material[^<]*</[^>]+>\s*<[^>]+>([^<]+)', obj_html)
                    if mat_m:
                        material = mat_m.group(1).strip()

                    collector._add(
                        "blm_karlsruhe", f"blm_{oid}", title, img,
                        source_url=obj_url,
                        museum="Badisches Landesmuseum Karlsruhe",
                        epoch=epoch, material=material,
                        search_query=query,
                    )
                    total += 1
                    await asyncio.sleep(config.RATE_LIMITS["scraper_delay"])
                except Exception as e:
                    logger.debug(f"Badisches LM obj: {e}")
                    continue

            await asyncio.sleep(config.RATE_LIMITS["scraper_delay"])
        except Exception as e:
            logger.debug(f"Badisches LM '{query}': {e}")

    logger.info(f"Badisches Landesmuseum (Scraper): {total}")
    return total


# =============================================================================
# HTML SCRAPER: DigiCult Saarland
# =============================================================================

async def scrape_digicult_saarland(session, collector):
    """Scrape saarland.digicult-museen.net fuer archaeologische Objekte."""
    total = 0
    queries = search_terms.QUERIES.get("digicult_saarland", [])
    base = "https://saarland.digicult-museen.net"

    for query in queries:
        try:
            url = f"{base}/objekte?term={quote_plus(query)}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    continue
                html = await resp.text()

            # Objektlinks finden
            links = re.findall(r'href="(/objekte/\d+)"', html)
            links = list(set(links))[:15]

            for link in links:
                try:
                    obj_url = f"{base}{link}"
                    async with session.get(obj_url, timeout=aiohttp.ClientTimeout(total=10)) as r2:
                        if r2.status != 200:
                            continue
                        obj_html = await r2.text()

                    # Titel
                    title = ""
                    t_m = re.search(r'<h1[^>]*>([^<]+)</h1>', obj_html)
                    if t_m:
                        title = t_m.group(1).strip()
                    if not title:
                        t_m = re.search(r'<title>([^<]+)</title>', obj_html)
                        title = t_m.group(1).strip().split(" - ")[0] if t_m else query

                    # Bild
                    img = ""
                    img_patterns = [
                        r'<img[^>]+class="[^"]*objekt[^"]*"[^>]+src="([^"]+)"',
                        r'<img[^>]+src="([^"]+/objekte/[^"]+\.(?:jpg|jpeg|png))"',
                        r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
                        r'<img[^>]+src="(https?://saarland\.digicult-museen\.net/[^"]+\.(?:jpg|jpeg|png))"',
                    ]
                    for pat in img_patterns:
                        img_m = re.search(pat, obj_html, re.IGNORECASE)
                        if img_m:
                            img = img_m.group(1)
                            if not img.startswith("http"):
                                img = f"{base}{img}"
                            break

                    if not img:
                        continue

                    # ID
                    oid_m = re.search(r'/objekte/(\d+)', link)
                    oid = oid_m.group(1) if oid_m else link.replace("/", "_")

                    # Museum-Name
                    museum = "DigiCult Saarland"
                    mu_m = re.search(r'Museum[^<]*</[^>]+>\s*<[^>]+>([^<]+)', obj_html)
                    if mu_m:
                        museum = mu_m.group(1).strip()

                    collector._add(
                        "digicult_saarland", f"dc_saar_{oid}", title, img,
                        source_url=obj_url, museum=museum, search_query=query,
                    )
                    total += 1
                    await asyncio.sleep(config.RATE_LIMITS["scraper_delay"])
                except Exception:
                    continue

            await asyncio.sleep(config.RATE_LIMITS["scraper_delay"])
        except Exception as e:
            logger.debug(f"DigiCult Saarland '{query}': {e}")

    logger.info(f"DigiCult Saarland (Scraper): {total}")
    return total


# =============================================================================
# HTML SCRAPER: CoinHirsch Auktionen
# =============================================================================

async def scrape_coinhirsch(session, collector):
    """Scrape coinhirsch.bidinside.com fuer antike Fibeln."""
    total = 0
    queries = search_terms.QUERIES.get("coinhirsch", [])
    base = "https://coinhirsch.bidinside.com"

    for query in queries:
        try:
            url = f"{base}/?searchterm={quote_plus(query)}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15),
                                   headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status != 200:
                    continue
                html = await resp.text()

            # Lots/Items finden
            items = re.findall(
                r'<div[^>]*class="[^"]*lot[^"]*"[^>]*>.*?'
                r'<a[^>]+href="([^"]+)"[^>]*>.*?'
                r'<img[^>]+src="([^"]+)".*?'
                r'(?:<[^>]+>)*([^<]{5,100})',
                html, re.DOTALL
            )

            if not items:
                # Alternativer Pattern
                links = re.findall(r'href="([^"]*lot[^"]*)"', html)
                imgs = re.findall(r'<img[^>]+src="(https?://[^"]+\.(?:jpg|jpeg|png))"', html, re.IGNORECASE)
                titles = re.findall(r'class="[^"]*title[^"]*"[^>]*>([^<]+)', html)
                items = list(zip(links[:20], imgs[:20], titles[:20]))

            for href, img, title in items[:20]:
                title = re.sub(r'<[^>]+>', '', title).strip()
                if not title or not img:
                    continue

                # Nur Fibeln/relevante Objekte
                title_lower = title.lower()
                relevant = any(kw in title_lower for kw in [
                    "fibel", "fibula", "brosche", "brooch", "gewandnadel",
                    "spange", "gewandschmuck",
                ])
                if not relevant:
                    continue

                if not img.startswith("http"):
                    img = f"{base}/{img.lstrip('/')}"
                if not href.startswith("http"):
                    href = f"{base}/{href.lstrip('/')}"

                oid = re.search(r'(\d+)', href)
                oid = oid.group(1) if oid else str(hash(title))[:10]

                collector._add(
                    "coinhirsch", f"ch_{oid}", title, img,
                    source_url=href, museum="CoinHirsch Auktionen",
                    search_query=query,
                )
                total += 1

            await asyncio.sleep(config.RATE_LIMITS["scraper_delay"])
        except Exception as e:
            logger.debug(f"CoinHirsch '{query}': {e}")

    logger.info(f"CoinHirsch (Scraper): {total}")
    return total


# =============================================================================
# EUROPEANA QUERY: Neue Museen
# =============================================================================

async def collect_new_europeana_museums(session, collector):
    """Sucht Fibeln in neuen Museen via Europeana Provider-Queries."""
    total = 0
    eu_key = config.API_KEYS.get("europeana", "")
    if not eu_key:
        return

    for source_name, queries in EU_MUSEUM_QUERIES_NEW.items():
        source_count = 0
        for query in queries:
            try:
                params = {
                    "wskey": eu_key,
                    "query": query,
                    "rows": 100,
                    "profile": "rich",
                    "qf": "TYPE:IMAGE",
                }
                async with session.get(
                    "https://api.europeana.eu/record/v2/search.json",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    if not isinstance(data, dict):
                        continue

                    for item in data.get("items", []):
                        img = None
                        if item.get("edmIsShownBy"):
                            img = item["edmIsShownBy"][0] if isinstance(item["edmIsShownBy"], list) else item["edmIsShownBy"]
                        if not img and item.get("edmPreview"):
                            img = item["edmPreview"][0] if isinstance(item["edmPreview"], list) else item["edmPreview"]

                        if img:
                            title = ""
                            if item.get("title"):
                                title = item["title"][0] if isinstance(item["title"], list) else item["title"]

                            thumb = ""
                            if item.get("edmPreview"):
                                thumb = item["edmPreview"][0] if isinstance(item["edmPreview"], list) else item["edmPreview"]

                            museum = ""
                            if item.get("dataProvider"):
                                museum = item["dataProvider"][0] if isinstance(item["dataProvider"], list) else item["dataProvider"]

                            collector._add(
                                source_name, item.get("id", ""),
                                title, img,
                                thumbnail_url=thumb,
                                source_url=item.get("guid", ""),
                                museum=museum,
                                search_query=query,
                            )
                            source_count += 1
                            total += 1

                await asyncio.sleep(config.RATE_LIMITS["europeana_delay"])
            except Exception as e:
                logger.debug(f"EU-New '{source_name}' '{query[:30]}': {e}")

        if source_count > 0:
            logger.info(f"Europeana-Neu {source_name}: {source_count}")

    logger.info(f"Neue Europeana-Museen total: {total}")
    return total


# =============================================================================
# MAIN INTEGRATION
# =============================================================================

async def collect_new_sources(session, collector) -> int:
    """
    Ruft alle neuen Quellen auf.
    Wird von museum_apis.py -> MuseumCollector.collect_all() aufgerufen.
    """
    total = 0

    tasks = [
        collect_new_europeana_museums(session, collector),
        scrape_badisches_lm(session, collector),
        scrape_digicult_saarland(session, collector),
        scrape_coinhirsch(session, collector),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, int):
            total += r
        elif isinstance(r, Exception):
            logger.error(f"Neue Quellen: {type(r).__name__}: {r}")

    logger.info(f"=== NEUE QUELLEN GESAMT: {total} ===")
    return total
