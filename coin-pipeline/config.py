"""
ArchaeoFinder — Muenz-Pipeline Konfiguration v4.0.0
=====================================================
UPGRADE: ViT-L-14-336 @ 336px
"""
import os
import search_terms

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://neyudzqjqbqfaxbfnglx.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# === CLIP MODEL — ViT-L-14-336 @ 336px ===
CLIP_MODEL = os.getenv("CLIP_MODEL", "ViT-L-14-336")
CLIP_PRETRAINED = os.getenv("CLIP_PRETRAINED", "openai")
EMBEDDING_DIM = 768

# === GPU — angepasst fuer 336px ===
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "128"))
IMAGE_SIZE = 336
MAX_VRAM_USAGE = 0.80
PREFETCH_FACTOR = int(os.getenv("PREFETCH_FACTOR", "6"))
PREPROCESS_THREADS = int(os.getenv("PREPROCESS_THREADS", "8"))

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "32"))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "10"))
MAX_IMAGE_SIZE_MB = 15
IMAGE_CACHE_DIR = "/app/data/images"
IMAGES_DIR = IMAGE_CACHE_DIR

SUPABASE_TABLE = "coin_embeddings"
UPLOAD_BATCH_SIZE = int(os.getenv("UPLOAD_BATCH_SIZE", "50"))

PIPELINE_VERSION = "4.0.0"
PIPELINE_TYPE = "coins"

API_KEYS = {
    "europeana": os.getenv("EUROPEANA_API_KEY", "asishamp"),
    "harvard": os.getenv("HARVARD_API_KEY", ""),
    "rijksmuseum": os.getenv("RIJKSMUSEUM_API_KEY", ""),
    "smithsonian": os.getenv("SMITHSONIAN_API_KEY", ""),
    "ddb": os.getenv("DDB_API_KEY", "pVMbvzbKl91A5Wf3eqjP3YOcXOxssLO2ouc2seKf7hLRoU6AXLQ1772056103933"),
}

SEARCH_QUERIES = search_terms.QUERIES

# === RATE LIMITS — KOMPLETT ===
RATE_LIMITS = {
    "europeana_delay": 0.2,
    "default_delay": 0.3,
    "slow_delay": 0.5,
    "scraper_delay": 1.0,
    "met_query_delay": 0.5,
    "met_object_delay": 0.1,
    "europeana_rows": 100,
    "europeana_max_per_query": 1000,
    "met_max_per_query": 80,
    "met_max_objects": 80,
    "ddb_rows": 100,
    "ddb_max_per_query": 500,
    "max_per_query": 100,
    "cleveland_pages": 2,
    "chicago_pages": 2,
    "va_page_size": 100,
    "smithsonian_rows": 100,
}

# === Coin-spezifische Configs ===
EUROPEANA_CONFIG = {
    "rows_per_page": 100,
    "max_per_query": 1000,
    "delay": 0.2,
}

MET_CONFIG = {
    "max_objects_per_query": 80,
    "object_delay": 0.1,
    "query_delay": 0.5,
}

PAS_CONFIG = {
    "base_url": "https://finds.org.uk/database/ajax/search",
    "max_results": 500,
    "records_per_page": 100,
    "periods": [
        "IRON AGE", "ROMAN", "EARLY MEDIEVAL", "MEDIEVAL",
        "POST MEDIEVAL", "GREEK AND ROMAN PROVINCIAL",
        "BYZANTINE", "UNKNOWN",
    ],
    "image_base_url": "https://finds.org.uk",
}

BM_CONFIG = {
    "search_url": "https://www.britishmuseum.org/api/_search",
    "collection_url": "https://www.britishmuseum.org/collection",
    "max_results_per_query": 100,
}

DDB_CONFIG = {
    "api_url": "https://api.deutsche-digitale-bibliothek.de",
    "search_endpoint": "/search",
    "item_endpoint": "/items",
    "rows_per_request": 100,
    "max_rows": 1000,
}

MUSEUM_DIGITAL_CONFIG = {
    "instances": [
        "https://nat.museum-digital.de",
        "https://hessen.museum-digital.de",
        "https://nrw.museum-digital.de",
        "https://sachsen-anhalt.museum-digital.de",
        "https://sachsen.museum-digital.de",
        "https://thueringen.museum-digital.de",
        "https://rlp.museum-digital.de",
        "https://berlin.museum-digital.de",
        "https://bayern.museum-digital.de",
        "https://bw.museum-digital.de",
        "https://westfalen.museum-digital.de",
        "https://brandenburg.museum-digital.de",
        "https://mecklenburg-vorpommern.museum-digital.de",
        "https://schleswig-holstein.museum-digital.de",
        "https://niedersachsen.museum-digital.de",
        "https://hamburg.museum-digital.de",
    ],
    "per_page": 50,
    "max_results": 200,
}

DIGICULT_CONFIG = {
    "europeana_providers": [
        "Muenzkabinett Berlin",
        "Landesmuseum Schleswig-Holstein",
        "Landesamt fuer Denkmalpflege und Archaeologie Sachsen-Anhalt",
        "Museum fuer Vor- und Fruehgeschichte",
        "Historisches Museum der Pfalz",
        "Landesmuseum fuer Vorgeschichte Halle",
    ],
}

FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "5.0"))
SAVE_INTERVAL = float(os.getenv("SAVE_INTERVAL", "300.0"))
