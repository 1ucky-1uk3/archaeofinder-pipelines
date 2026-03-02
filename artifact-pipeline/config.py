"""
ArchaeoFinder — Artefakt-Pipeline Konfiguration v4.0.0
=======================================================
UPGRADE: ViT-L-14-336 @ 336px
Allgemeine Artefakte (Steinbeile, Keramik, Werkzeuge, etc.)
"""
import os

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

SUPABASE_TABLE = "artifact_embeddings"
UPLOAD_BATCH_SIZE = int(os.getenv("UPLOAD_BATCH_SIZE", "50"))

PIPELINE_VERSION = "4.0.0"
PIPELINE_TYPE = "artifacts"

API_KEYS = {
    "europeana": os.getenv("EUROPEANA_API_KEY", "asishamp"),
    "harvard": os.getenv("HARVARD_API_KEY", ""),
    "rijksmuseum": os.getenv("RIJKSMUSEUM_API_KEY", ""),
    "smithsonian": os.getenv("SMITHSONIAN_API_KEY", ""),
    "ddb": os.getenv("DDB_API_KEY", "pVMbvzbKl91A5Wf3eqjP3YOcXOxssLO2ouc2seKf7hLRoU6AXLQ1772056103933"),
}

RATE_LIMITS = {
    "europeana_delay": 0.2,
    "default_delay": 0.3,
    "slow_delay": 0.5,
    "scraper_delay": 1.0,
    "europeana_rows": 100,
    "europeana_max_per_query": 1000,
    "met_max_per_query": 80,
    "met_max_objects": 80,
    "met_query_delay": 0.5,
    "met_object_delay": 0.1,
    "ddb_rows": 100,
    "ddb_max_per_query": 500,
    "max_per_query": 100,
    "cleveland_pages": 2,
    "chicago_pages": 2,
    "va_page_size": 100,
    "smithsonian_rows": 100,
}

# Breite Europeana-Queries fuer allgemeine Artefakte
EUROPEANA_BROAD_QUERIES = [
    "archaeological artifact",
    "Steinbeil archaeologie",
    "Keramik archaeologisch",
    "Bronze Werkzeug antik",
    "Pfeilspitze archaeologie",
    "Axt Bronze Steinzeit",
    "Tonscherbe archaeologisch",
    "Gefaess archaeologie",
    "Schmuck archaeologisch antik",
    "Waffe archaeologie Bronze Eisen",
    "Fibel Brosche antik",
    "Muenze antik archaeologie",
    "archaeological pottery",
    "ancient bronze tool",
    "stone age artifact",
    "medieval artifact",
    "roman artifact",
    "iron age artifact",
    "neolithic tool",
    "archaeological find",
]

MAX_ITEMS_PER_SOURCE = int(os.getenv("MAX_ITEMS_PER_SOURCE", "10000"))

MUSEUM_DIGITAL_INSTANCES = [
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
]

FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "5.0"))
SAVE_INTERVAL = float(os.getenv("SAVE_INTERVAL", "300.0"))
