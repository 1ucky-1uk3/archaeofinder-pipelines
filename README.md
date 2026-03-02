# ArchaeoFinder v4.0.0 — ViT-L-14-336 @ 336px

## Alle 3 Pipelines auf ViT-L-14-336 upgraden

### Dateistruktur

```
archaeofinder-pipelines-v4.0.0/
|
+-- fibel-pipeline/
|   +-- config.py              # v4.0.0 — ViT-L-14-336 + ALLE fehlenden Config-Keys
|   +-- docker-compose.yml     # Angepasst fuer 336px
|   +-- Dockerfile
|   +-- requirements.txt
|   (embedder.py, pipeline.py, museum_apis.py, search_terms.py,
|    neue_quellen.py, uploader.py — aus vorherigem Chat uebernehmen)
|
+-- coin-pipeline/
|   +-- config.py              # v4.0.0 — ViT-L-14-336 + alle Configs
|   +-- docker-compose.yml
|   +-- Dockerfile
|   +-- requirements.txt
|   (pipeline.py, search_terms.py, neue_quellen_coins.py — unveraendert)
|
+-- artifact-pipeline/
|   +-- config.py              # v4.0.0 — ViT-L-14-336
|   +-- docker-compose.yml
|   +-- Dockerfile
|   +-- requirements.txt
|   (pipeline.py, museum_apis.py, uploader.py, supabase-setup.sql — unveraendert)
|
+-- DEPLOY.md                  # Deployment-Anleitung
+-- README.md                  # Diese Datei
```

### Was wurde geaendert?

NUR die folgenden Dateien sind neu/geaendert:
- **config.py** (alle 3 Pipelines) — Modell + fehlende Config-Keys
- **docker-compose.yml** (alle 3) — CLIP_MODEL env var
- **Dockerfile** (alle 3) — Identisch
- **requirements.txt** (alle 3) — Identisch
- **embedder.py** (nur Fibel) — 336px Anpassungen (aus vorherigem Chat)

Alle anderen Dateien (pipeline.py, museum_apis.py, search_terms.py,
neue_quellen.py, uploader.py) bleiben UNVERAENDERT von v3.5.1.
