# ArchaeoFinder v4.0.0 — Deployment Guide
## UPGRADE: ViT-L-14-336 @ 336px (alle 3 Pipelines)

## Was ist neu in v4.0.0?

### Modell-Upgrade: ViT-L-14-336 @ 336px
- **Vorher**: ViT-L-14 @ 224px = 16x16 = 256 Patches
- **Jetzt**: ViT-L-14-336 @ 336px = 24x24 = 576 Patches
- **2.25x mehr visuelle Details** bei gleicher 768d Embedding-Dimension
- DB-kompatibel: Bestehende Tabellen koennen weiterverwendet werden
- UPSERT ueberschreibt alte 224px Embeddings automatisch

### Config-Fix (kritisch!)
- RATE_LIMITS: Alle 11+ Keys komplett (europeana_max_per_query, ddb_max_per_query, etc.)
- DIMU_MAX_ROWS + DIMU_API_KEY: Waren fehlend -> digitalt_museum 0 Items
- BATCH_SIZE: 128 default (statt 256) fuer 336px VRAM-Bedarf
- Dynamische Batch-Anpassung bei OOM

---

## WICHTIG: Vor dem Deploy

```bash
# 1. Alten Bild-Cache loeschen (werden in q90 neu heruntergeladen)
sudo rm -rf ~/archaeofinder-fibel-pipeline/data/images/*
sudo rm -rf ~/coin-finder/data/images/*

# 2. Alte Embedding-Caches loeschen
sudo rm -f ~/archaeofinder-fibel-pipeline/data/cache/embedded_items.json
sudo rm -f ~/archaeofinder-fibel-pipeline/data/cache/embedded_items_partial.json
sudo rm -f ~/coin-finder/data/cache/embedded_items.json
sudo rm -f ~/coin-finder/data/cache/embedded_items_partial.json

# collected_items.json kann bleiben!
```

---

## Deploy: Fibel-Pipeline

```bash
cd ~/archaeofinder-fibel-pipeline/
# config.py aus ZIP/fibel-pipeline/ kopieren (KRITISCH!)
sudo docker compose build --no-cache
sudo docker compose run --rm fibel-pipeline python3 pipeline.py --mode full
```

## Deploy: Coin-Pipeline

```bash
cd ~/coin-finder/
# config.py aus ZIP/coin-pipeline/ kopieren (KRITISCH!)
sudo docker compose build --no-cache
sudo docker compose run --rm coin-pipeline python3 pipeline.py --mode full
```

## Deploy: Artifact-Pipeline

```bash
cd ~/archaeofinder-artifact-pipeline/
# Alle Dateien aus ZIP/artifact-pipeline/ kopieren
sudo docker compose build --no-cache
sudo docker compose run --rm artifact-pipeline python3 pipeline.py --mode full
```

---

## GPU-spezifische Batch-Konfiguration

```bash
# RTX 3060/3070 (8 GB)
BATCH_SIZE=64 sudo docker compose run --rm <pipeline> python3 pipeline.py --mode full

# RTX 3080/3080Ti (10-12 GB) — Default
BATCH_SIZE=128 sudo docker compose run --rm <pipeline> python3 pipeline.py --mode full

# RTX 3090/4090 (24 GB) — Maximale Geschwindigkeit
BATCH_SIZE=256 sudo docker compose run --rm <pipeline> python3 pipeline.py --mode full
```

---

## Verifikation nach Update

```sql
-- Pruefen welche Modelle in der DB sind
SELECT embedding_model, pipeline_version, COUNT(*)
FROM fibula_embeddings
GROUP BY embedding_model, pipeline_version;

SELECT embedding_model, pipeline_version, COUNT(*)
FROM coin_embeddings
GROUP BY embedding_model, pipeline_version;

-- Erwartung: nur ViT-L-14-336/openai + 4.0.0
```

---

## Vergleich v3.5.1 vs v4.0.0

| Parameter          | v3.5.1 (ViT-L-14) | v4.0.0 (ViT-L-14-336) |
|--------------------|--------------------|------------------------|
| Modell             | ViT-L-14           | ViT-L-14-336           |
| Bildgroesse        | 224x224px          | 336x336px              |
| Patches            | 16x16 = 256        | 24x24 = 576            |
| Pixeldaten         | 1x                 | 2.25x                  |
| Embedding-Dim      | 768d               | 768d (kompatibel!)     |
| Default Batch      | 256                | 128                    |
| VRAM (Batch=128)   | ~1.8 GB            | ~4.2 GB                |
| Cache JPEG-Qual.   | 85                 | 90                     |
| Min Bildgroesse    | 1000 bytes         | 2000 bytes             |
| Europeana          | 0 Items (Bug!)     | 1000/Query (gefixt!)   |
| DDB                | 0 Items (Bug!)     | 500/Query (gefixt!)    |
| DiMu               | 0 Items (Bug!)     | Funktioniert (gefixt!) |
