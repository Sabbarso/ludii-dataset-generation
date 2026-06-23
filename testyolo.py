"""
Test YOLOv8 sur images reelles + Detection AMELIOREE de la taille du plateau
"""

from ultralytics import YOLO
import os
from PIL import Image
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

MODEL_PATH = "chess_ludii_best.pt"
TEST_IMAGES = ["chess2.png", "test_chess.png"]
OUTPUT_DIR = "test_results"

CLASS_NAMES = [
    "white_king", "white_queen", "white_rook", "white_bishop",
    "white_knight", "white_pawn",
    "black_king", "black_queen", "black_rook", "black_bishop",
    "black_knight", "black_pawn"
]

CONFIDENCE = 0.5  # augmente pour eviter les faux positifs

# ============================================================================
# DETECTION TAILLE PLATEAU - METHODE AMELIOREE
# ============================================================================

def detect_board_size(boxes, img_width, img_height):
    """
    Estime cols x rows en utilisant la distance entre centres de pieces.
    Plus fiable que de mesurer la taille des bounding boxes.
    """
    if len(boxes) < 4:
        return None, None
    
    # Extraire tous les centres
    centers = []
    for box in boxes:
        x, y, w, h = box.xywh[0].tolist()
        centers.append((x, y))
    
    # Toutes les coordonnees X et Y uniques (arrondies pour grouper)
    xs = sorted([c[0] for c in centers])
    ys = sorted([c[1] for c in centers])
    
    # Trouver les ecarts entre voisins
    def get_min_gap(values, min_threshold=10):
        gaps = []
        for i in range(len(values) - 1):
            gap = values[i+1] - values[i]
            if gap > min_threshold:
                gaps.append(gap)
        return gaps
    
    gaps_x = get_min_gap(xs)
    gaps_y = get_min_gap(ys)
    
    if not gaps_x or not gaps_y:
        return None, None
    
    # Taille d'une case = mediane des ecarts (robuste aux outliers)
    cell_size_x = np.median(gaps_x)
    cell_size_y = np.median(gaps_y)
    cell_size = (cell_size_x + cell_size_y) / 2
    
    # Plage des centres
    range_x = max(xs) - min(xs)
    range_y = max(ys) - min(ys)
    
    # Estimer dimensions
    estimated_cols = round(range_x / cell_size) + 1
    estimated_rows = round(range_y / cell_size) + 1
    
    return estimated_cols, estimated_rows

def guess_variant(cols, rows, num_pieces, has_bishop, has_pawn):
    """Estime la variante a partir des caracteristiques."""
    if cols == 8 and rows == 8:
        return "Standard Chess (8x8)"
    elif (cols == 8 and rows == 4) or (cols == 4 and rows == 8):
        return "Half Chess (8x4)"
    elif cols == 6 and rows == 6:
        return "Los Alamos Chess (6x6, sans bishops)"
    elif cols == 9 and rows == 8:
        return "Symmetric Chess (9x8)"
    elif cols == 16 and rows == 12:
        return "Double Chess (16x12)"
    else:
        return f"Plateau {cols}x{rows} - non identifie"

# ============================================================================
# MAIN
# ============================================================================

print("=" * 70)
print("TEST YOLOV8 SUR IMAGES REELLES")
print(f"Seuil de confiance : {CONFIDENCE}")
print("=" * 70)

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"\nChargement du modele : {MODEL_PATH}")
model = YOLO(MODEL_PATH)
print("OK - Modele charge")

for img_name in TEST_IMAGES:
    if not os.path.exists(img_name):
        print(f"\n[ERREUR] Image introuvable : {img_name}")
        continue
    
    print(f"\n{'=' * 70}")
    print(f"IMAGE : {img_name}")
    print(f"{'=' * 70}")
    
    img_pil = Image.open(img_name)
    img_w, img_h = img_pil.size
    print(f"Dimensions image       : {img_w} x {img_h} pixels")
    
    results = model.predict(img_name, conf=CONFIDENCE, verbose=False)
    result = results[0]
    
    # Detection taille plateau
    cols, rows = detect_board_size(result.boxes, img_w, img_h)
    
    # Comptage par classe et type
    class_counts = {}
    type_counts = {}
    confidences = []
    
    for box in result.boxes:
        cls_id = int(box.cls[0])
        cls_name = CLASS_NAMES[cls_id]
        piece_type = cls_name.replace("white_", "").replace("black_", "")
        
        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
        type_counts[piece_type] = type_counts.get(piece_type, 0) + 1
        confidences.append(float(box.conf[0]))
    
    total = len(result.boxes)
    has_bishop = type_counts.get("bishop", 0) > 0
    has_pawn = type_counts.get("pawn", 0) > 0
    
    print(f"\nPLATEAU DETECTE")
    print(f"  Cols x Rows estime   : {cols} x {rows}")
    print(f"  Cases estimees       : {cols * rows if cols and rows else 'N/A'}")
    
    if cols and rows:
        variant = guess_variant(cols, rows, total, has_bishop, has_pawn)
        print(f"  Variante probable    : {variant}")
    
    print(f"\nPIECES")
    print(f"  Total detectees      : {total}")
    
    if total > 0:
        avg_conf = sum(confidences) / len(confidences)
        print(f"  Confiance moyenne    : {avg_conf:.3f}")
        
        white_count = sum(c for cls, c in class_counts.items() if cls.startswith("white"))
        black_count = sum(c for cls, c in class_counts.items() if cls.startswith("black"))
        print(f"  Blanches             : {white_count}")
        print(f"  Noires               : {black_count}")
        
        print(f"\n  Par type (toutes couleurs) :")
        for piece_type in sorted(type_counts.keys()):
            print(f"    {piece_type:<10} : {type_counts[piece_type]}")
    
    # Sauvegarder
    output_path = os.path.join(OUTPUT_DIR, f"PRED_{img_name}")
    annotated = result.plot()
    annotated_rgb = annotated[..., ::-1]
    Image.fromarray(annotated_rgb).save(output_path)
    print(f"\n  Image annotee        : {output_path}")

print(f"\n{'=' * 70}")
print("TERMINE")
print(f"{'=' * 70}")