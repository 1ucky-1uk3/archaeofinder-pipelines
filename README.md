# ArchaeoFinder ML Pipelines

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](https://archaeofinder.de)
[![Model](https://img.shields.io/badge/model-ViT--L--14--336-orange.svg)](README.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Machine Learning Pipelines für die KI-gestützte Archäologie-Fundbestimmung

## 🏺 Über ArchaeoFinder

ArchaeoFinder nutzt State-of-the-Art Computer Vision Modelle zur automatischen Feature-Extraktion aus archäologischen Artefakten. Dieses Repository enthält die ML Pipelines für Bildverarbeitung und Vektor-Embeddings.

**Live:** [archaeofinder.de](https://archaeofinder.de)

## 🧠 Modell-Architektur

### Vision Transformer (ViT-L-14-336)

- **Modell:** OpenAI CLIP ViT-L/14 @ 336px
- **Eingabe:** 336×336 Pixel Bilder
- **Ausgabe:** 768-dimensionale Vektoren
- **Use Case:** Visuelle Ähnlichkeitssuche

```
Bild (336×336) → ViT Encoder → 768-d Vector → Vector DB
```

## ✨ Features

- 🎯 **Feature Extraction** – 768-d Embeddings aus Bildern
- 🔄 **Batch Processing** – Effiziente Massenverarbeitung
- 📊 **Vector Normalisierung** – Optimiert für Ähnlichkeitssuche
- 🚀 **GPU Acceleration** – CUDA Unterstützung
- 🔧 **Fine-Tuning** – Domain-Specific Training

## 🚀 Schnellstart

### Voraussetzungen

- Python 3.9+
- CUDA 11.8+ (optional, für GPU)
- 8GB+ RAM (16GB empfohlen)

### Installation

```bash
# Repository klonen
git clone https://github.com/1ucky-1uk3/archaeofinder-pipelines.git
cd archaeofinder-pipelines

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Modell-Download (automatisch beim ersten Start)
python download_models.py
```

### Inference API starten

```bash
# Server starten
python serve.py --port 5000

# Oder mit Docker
docker build -t archaeofinder-ml .
docker run -p 5000:5000 --gpus all archaeofinder-ml
```

## 🏗️ Pipeline-Architektur

```
pipelines/
├── preprocessing/          # Bildvorverarbeitung
│   ├── resize.py          # 336×336 Normalisierung
│   ├── augment.py         # Data Augmentation
│   └── normalize.py       # Farb-/Kontrastanpassung
├── embedding/             # Feature-Extraktion
│   ├── vit_encoder.py     # ViT Modell Wrapper
│   └── batch_processor.py # Batch Inference
├── similarity/            # Ähnlichkeitsberechnung
│   ├── cosine.py          # Cosine Similarity
│   └── faiss_index.py     # FAISS Vector Index
└── training/              # Fine-Tuning
    ├── dataset.py         # Custom Dataset Loader
    └── train.py           # Training Loop
```

## 🔌 API Usage

### Einzelnes Bild
```python
import requests

response = requests.post(
    "http://localhost:5000/embed",
    files={"image": open("artifact.jpg", "rb")}
)

embedding = response.json()["embedding"]
# 768-dimensionaler Vektor
```

### Batch Processing
```python
import requests

images = [("file1.jpg", open("1.jpg", "rb")), ...]
response = requests.post(
    "http://localhost:5000/embed/batch",
    files=images
)
```

## 📊 Performance

| Metrik | CPU | GPU (RTX 3090) |
|--------|-----|----------------|
| Inference/Bild | ~500ms | ~50ms |
| Batch (32) | ~15s | ~1.5s |
| Speicher | 4GB | 8GB |

## 🛠️ Tech Stack

- **Framework:** PyTorch 2.0+
- **Model:** OpenAI CLIP ViT-L/14-336
- **Vector Search:** FAISS
- **API:** FastAPI
- **Deployment:** Docker, Kubernetes

## 🔧 Konfiguration

```yaml
# config.yaml
model:
  name: "ViT-L-14-336"
  checkpoint: "openai/clip-vit-large-patch14-336"
  
preprocessing:
  input_size: [336, 336]
  normalize:
    mean: [0.48145466, 0.4578275, 0.40821073]
    std: [0.26862954, 0.26130258, 0.27577711]
    
inference:
  batch_size: 32
  device: "cuda"  # oder "cpu"
  precision: "fp16"
```

## 🧪 Tests

```bash
# Modell-Tests
pytest tests/test_model.py -v

# Integration Tests
pytest tests/test_api.py -v

# Benchmark
python benchmark.py --images test_data/
```

## 📈 Fine-Tuning

Für domain-spezifisches Training:

```bash
# Dataset vorbereiten
python prepare_dataset.py --input raw_data/ --output dataset/

# Training starten
python train.py \
  --data dataset/ \
  --epochs 10 \
  --lr 1e-5 \
  --output checkpoints/
```

## 📋 Roadmap

- [ ] Multi-Scale Embeddings (224px + 336px + 448px)
- [ ] ONNX Export für Edge Deployment
- [ ] Quantization (INT8) für mobile Geräte
- [ ] Active Learning Pipeline
- [ ] AutoML für Hyperparameter-Optimierung

## 📚 Referenzen

- [CLIP Paper](https://arxiv.org/abs/2103.00020)
- [Vision Transformers](https://arxiv.org/abs/2010.11929)
- [FAISS Documentation](https://faiss.ai/)

## 🤝 Mitwirken

1. Fork erstellen
2. Feature-Branch: `git checkout -b feature/neues-modell`
3. Committen: `git commit -am 'Neues Modell-Feature'`
4. Pushen: `git push origin feature/neues-modell`
5. Pull Request erstellen

## 📄 Lizenz

MIT License – siehe [LICENSE](LICENSE)

## 🔗 Verwandte Projekte

- [Frontend](https://github.com/1ucky-1uk3/archaeofinder-frontend)
- [Backend](https://github.com/1ucky-1uk3/archaeofinder-backend)

---

**ArchaeoFinder** – KI für die Archäologie 🏺

*Powered by OpenAI CLIP ViT-L/14-336*
