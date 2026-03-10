"""
ArchaeoFinder — Fibel-Pipeline Konfiguration v4.1.0
=====================================================
SPEED OPTIMIZATION: ViT-B-32 @ 224px (statt ViT-L-14-336)

v4.1.0 Aenderungen:
  - CLIP_MODEL: ViT-B-32 (2x schneller als ViT-L-14)
  - IMAGE_SIZE: 224px (schnellere Verarbeitung)
  - BATCH_SIZE: 256 (höher durch kleineres Modell)
  - EMBEDDING_DIM: 512 (statt 768, immer noch gut für Ähnlichkeit)

Performance: ~2-3 Sekunden statt 5-10 Sekunden pro Bild
"""
import os
import search_terms

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://neyudzqjqbqfaxbfnglx.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# === CLIP MODEL — ViT-B-32 @ 224px (Schnell!) ===
CLIP_MODEL = os.getenv("CLIP_MODEL", "ViT-B-32")  # GEÄNDERT: Schnelleres Modell
CLIP_PRETRAINED = os.getenv("CLIP_PRETRAINED", "openai")
EMBEDDING_DIM = 512  # GEÄNDERT: 512 für B-32 (war 768 für L-14)

# === GPU BATCH PROCESSING — optimiert für B-32 ===
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "256"))  # GEÄNDERT: Höher durch kleineres Modell
IMAGE_SIZE = 224  # GEÄNDERT: 224px statt 336px
MAX_VRAM_USAGE = 0.80
PREFETCH_FACTOR = int(os.getenv("PREFETCH_FACTOR", "8"))  # GEÄNDERT: Höher
PREPROCESS_THREADS = int(os.getenv("PREPROCESS_THREADS", "8"))

# --- Async Download ---
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "32"))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "10"))
MAX_IMAGE_SIZE_MB = 15
IMAGE_CACHE_DIR = "/app/data/images"
IMAGES_DIR = IMAGE_CACHE_DIR

# --- Supabase Tabelle ---
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "fibula_embeddings")
UPLOAD_BATCH_SIZE = int(os.getenv("UPLOAD_BATCH_SIZE", "50"))

# --- Pipeline Info ---
PIPELINE_VERSION = "4.1.0"
PIPELINE_TYPE = "fibeln"

# --- API Keys ---
API_KEYS = {
    "europeana": os.getenv("EUROPEANA_API_KEY", "asishamp"),
    "harvard": os.getenv("HARVARD_API_KEY", ""),
    "rijksmuseum": os.getenv("RIJKSMUSEUM_API_KEY", ""),
    "smithsonian": os.getenv("SMITHSONIAN_API_KEY", ""),
    "ddb": os.getenv("DDB_API_KEY", "pVMbvzBKl91A5Wf3eqjP3YOcXOxssLO2ouc2seKf7hLRoU6AXLQ1772056103933"),
}

# --- Suchbegriffe ---
SEARCH_QUERIES = search_terms.QUERIES

# === RATE LIMITS — KOMPLETT (alle 11 Keys!) ===
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
    "ddb_rows": 100,
    "ddb_max_per_query": 500,
    "max_per_query": 100,
    "met_max_objects": 80,
    "cleveland_pages": 2,
    "chicago_pages": 2,
    "va_page_size": 100,
    "smithsonian_rows": 100,
}

# === DiMu (DigitalMuseum) ===
DIMU_API_URL = os.getenv("DIMU_API_URL", "https://api.dimu.org/api/search")
DIMU_API_KEY = os.getenv("DIMU_API_KEY", "demo")
DIMU_IMG_BASE = "https://dms01.dimu.org/image"
DIMU_MAX_PAGES = int(os.getenv("DIMU_MAX_PAGES", "10"))
DIMU_MAX_ROWS = int(os.getenv("DIMU_MAX_ROWS", "100"))
DIMU_PAGE_SIZE = 50

# === museum-digital.de ===
MUSEUM_DIGITAL_MAX_PER_INSTANCE = int(os.getenv("MUSEUM_DIGITAL_MAX_PER_INSTANCE", "200"))
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
    "https://westfalen.museum-digital.de",
    "https://brandenburg.museum-digital.de",
    "https://mecklenburg-vorpommern.museum-digital.de",
    "https://schleswig-holstein.museum-digital.de",
    "https://niedersachsen.museum-digital.de",
    "https://hamburg.museum-digital.de",
]
MUSEUM_DIGITAL_PAGE_SIZE = 50
MUSEUM_DIGITAL_MAX_PAGES = 3

# === Weitere Quellen ===
ARCHIVE_API_URL = "https://arachne.dainst.org/data/search"
ARCHIVE_IMG_BASE = "https://arachne.dainst.org/data/image"
SOCH_API_URL = "http://www.kulturarvsdata.se/ksamsok/api"
POP_API_URL = "https://api.pop.culture.gouv.fr/search"

# --- Adaptive Flush ---
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "5.0"))
SAVE_INTERVAL = float(os.getenv("SAVE_INTERVAL", "300.0"))

# =============================================================================
# SEARCH OPTIMIZATION - Better similarity matching
# =============================================================================
SIMILARITY_THRESHOLD = 0.60       # Lowered from ~0.80 to capture more similar items
TOP_K_SEARCH_RESULTS = 50           # Increased from 10 for better comparison
DEBUG_EMBEDDINGS = True           # Enable detailed similarity debugging
SIMILARITY_LOG_PATH = "/app/logs/similarity.log"

# Weights for multi-factor similarity
SIMILARITY_GEOMETRIC_WEIGHT = 0.40
SIMILARITY_PATTERN_WEIGHT = 0.30
SIMILARITY_TEXTURE_WEIGHT = 0.30

# PERFORMANCE NOTES:
# - ViT-B-32: ~2-3 Sekunden pro Bild (schnell)
# - ViT-L-14: ~5-10 Sekunden pro Bild (langsam, bessere Qualität)
# - Für Produktion: B-32 ausreichend, L-14 nur wenn nötig
