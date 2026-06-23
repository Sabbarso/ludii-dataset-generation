# Ludii Dataset Generation & Object Detection (Vision Module)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Java](https://img.shields.io/badge/Java-17-orange?logo=openjdk&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple)
![Ludii](https://img.shields.io/badge/Ludii-1.3.14-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Computer-vision pipeline of the **Ludii Game Intelligence** platform: it generates a *synthetic, fully-annotated dataset* of board positions from the Ludii game engine and trains a **YOLOv8** detector to recognize pieces (class + position) from a board image.

> **Scope:** this repo covers the vision module only — dataset generation, annotation and object detection (everything up to and including YOLO). The knowledge graph, the QA module and the platform integration are documented in separate repositories.

---

## Why synthetic data?

No annotated dataset of board positions exists. The idea is to **render synthetic board images from the Ludii engine** — whose internal state is fully known — and to annotate them automatically for object detection. This gives perfect ground truth at scale.

## Pipeline

```
Ludii.jar (v1.3.14) — Java game engine
        │  Python ↔ Java bridge (JPype)
        ▼
Random game simulation (legal moves)
        ▼
Board state extraction (Ludii API)
        ▼
Image rendering — PNG 512×512 (Pillow)
        ▼
Annotation with Roboflow (YOLOv8 export)
        ▼
Train / Val / Test split
        ▼
Final dataset: 3,089 annotated images
```

## Tech Stack

| Component             | Tool                          | Version |
| --------------------- | ----------------------------- | ------- |
| Game engine           | Ludii (`Ludii-1.3.14.jar`)    | 1.3.14  |
| Java runtime          | JDK / JRE                     | 17      |
| Language              | Python                        | 3.11    |
| Java↔Python bridge    | JPype1                        | —       |
| Image rendering       | Pillow (PIL)                  | —       |
| Numerics              | NumPy                         | —       |
| Annotation            | Roboflow (web platform)       | —       |
| Detector framework    | Ultralytics YOLOv8            | 8.x     |
| Training hardware      | Kaggle GPU (NVIDIA Tesla T4) | —       |

> Freeze exact versions with `pip freeze > requirements.txt`.

## Dataset Composition

The first dataset version focuses on **chess and its variants**, chosen for the variety of board geometries.

| Variant            | Board          | Pieces | Images |
| ------------------ | -------------- | ------ | ------ |
| Chess              | 8 × 8 (64)     | 32     | 620    |
| Half Chess         | 8 × 4 (32)     | 16     | 620    |
| Los Alamos Chess   | 6 × 6 (36)     | 24     | 609    |
| Symmetric Chess    | 9 × 8 (72)     | 36     | 620    |
| Double Chess       | 16 × 12 (192)  | 64     | 620    |
| **Total**          |                |        | **3,089** |

**Split:** Train 80% (2,471) · Val 15% (463) · Test 5% (155)

**12 classes** (6 piece types × 2 colours):

```
0 white_king   1 white_queen  2 white_rook   3 white_bishop  4 white_knight  5 white_pawn
6 black_king   7 black_queen  8 black_rook   9 black_bishop 10 black_knight 11 black_pawn
```

## Setup

1. Install **Java 17** (required to run Ludii).
2. Download `Ludii-1.3.14.jar` from the [official portal](https://ludii.games/download.php) and place it in the project root.
3. Create a virtual environment and install dependencies:

```bash
python -m venv venv
# Windows:     venv\Scripts\activate
# Linux/Mac:   source venv/bin/activate
pip install JPype1 Pillow numpy ultralytics
```

## Usage

### 1. Generate the dataset

Run the generation scripts in order:

```
variant check → board geometry → random simulation → state extraction → rendering
```

The Ludii engine is driven from Python through JPype:

```python
import jpype
from jpype import JClass

jpype.startJVM(classpath=["Ludii-1.3.14.jar"])
GameLoader = JClass("other.GameLoader")
Trial      = JClass("other.trial.Trial")
Context    = JClass("other.context.Context")

game = GameLoader.loadGameFromName("Chess.lud")
```

For each variant, 20 games are simulated; at each turn a random legal move is applied, and every move yields one captured position — maximizing configuration diversity (dense openings to sparse endgames).

### 2. Annotate & export

Import the rendered images into [Roboflow](https://roboflow.com), label each piece with a bounding box + class, then export in **YOLOv8** format. A YOLO annotation line (coordinates normalized to `[0, 1]`):

```
class_id  x_center  y_center  width  height
```

Example `data.yaml`:

```yaml
path: /path/to/dataset
train: images/train
val: images/val
test: images/test
nc: 12
names: [white_king, white_queen, white_rook, white_bishop, white_knight,
        white_pawn, black_king, black_queen, black_rook, black_bishop,
        black_knight, black_pawn]
```

### 3. Train YOLOv8

Transfer learning from COCO-pretrained Nano weights:

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
model.train(
    data="data.yaml",
    epochs=50,      # early stopping enabled
    imgsz=512,
    batch=32,
)
```

| Parameter        | Value                          |
| ---------------- | ------------------------------ |
| Model            | YOLOv8n (Nano)                 |
| Initial weights  | COCO-pretrained (transfer)     |
| Platform         | Kaggle — NVIDIA Tesla T4       |
| Epochs           | 50 (max), early stopping       |
| Image size       | 512 px                         |
| Batch size       | 32                             |

## Results

On the synthetic test set:

| Metric            | Value  |
| ----------------- | ------ |
| mAP@0.5           | 0.9950 |
| mAP@0.5:0.95      | 0.9950 |
| Precision         | 0.9997 |
| Recall            | 1.0000 |

> These near-perfect scores validate the **internal consistency** of the pipeline. Generalization to real photographs is an open challenge (see below). Ultralytics artifacts (training curves, confusion matrix, sample predictions) live under `runs/detect/`.

## Known Limitations & Next Steps

- **Synthetic-to-real gap:** trained/tested on rendered images; performance drops on real photos (texture, lighting, perspective, shadows, piece styles).
- **Limited game family:** only chess variants so far.

Directions:
- Domain randomization in the renderer (textures, backgrounds, lighting, viewpoints)
- Stronger data augmentation during training
- Fine-tuning on a small set of real, annotated board images
- Extending the dataset to non-chess games available in Ludii

## Authors

- **Soukaina Sabbar** — [@Sabbarso](https://github.com/Sabbarso)
- **Salma Issam** — [@salma12814](https://github.com/salma12814)

ENSIAS — Data & Software Science

## Resources

- [Ludii portal](https://ludii.games/)
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [Roboflow](https://roboflow.com)
- [JPype](https://jpype.readthedocs.io/)
- [Pillow](https://python-pillow.org/)
