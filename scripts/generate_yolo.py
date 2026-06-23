import json
import os

# === CHEMINS ===
INPUT_JSON = r"C:\ludii\output\chess_positions.json"
LABELS_DIR = r"C:\ludii\output\labels"
os.makedirs(LABELS_DIR, exist_ok=True)

# === PARAMÈTRES DE L'IMAGE (doivent correspondre à render_image.py) ===
BOARD_SIZE = 512
CELL_SIZE = BOARD_SIZE // 8  # 64 pixels par case

# === MAPPING PIÈCE → CLASSE YOLO ===
# 12 classes (6 types × 2 couleurs)
PIECE_TO_CLASS = {
    "King1":   0,   # white_king
    "Queen1":  1,   # white_queen
    "Rook1":   2,   # white_rook
    "Bishop1": 3,   # white_bishop
    "Knight1": 4,   # white_knight
    "Pawn1":   5,   # white_pawn
    "King2":   6,   # black_king
    "Queen2":  7,   # black_queen
    "Rook2":   8,   # black_rook
    "Bishop2": 9,   # black_bishop
    "Knight2": 10,  # black_knight
    "Pawn2":   11,  # black_pawn
}

CLASS_NAMES = [
    "white_king", "white_queen", "white_rook", "white_bishop",
    "white_knight", "white_pawn",
    "black_king", "black_queen", "black_rook", "black_bishop",
    "black_knight", "black_pawn"
]

def case_to_pixel_center(case_index):
    """
    Retourne le centre pixel (x, y) d'une case Ludii.
    Case 0 = a1 (en bas à gauche), Case 63 = h8 (en haut à droite).
    """
    col = case_index % 8
    row = case_index // 8
    
    # En image, y=0 est en haut, donc on inverse la rangée
    pixel_x = col * CELL_SIZE + CELL_SIZE // 2
    pixel_y = (7 - row) * CELL_SIZE + CELL_SIZE // 2
    
    return pixel_x, pixel_y

def case_to_yolo_bbox(case_index, image_size=BOARD_SIZE):
    """
    Convertit une case Ludii en bounding box format YOLO.
    YOLO format : x_center y_center width height (tous normalisés 0-1)
    """
    pixel_x, pixel_y = case_to_pixel_center(case_index)
    
    # Normaliser entre 0 et 1
    x_center = pixel_x / image_size
    y_center = pixel_y / image_size
    
    # La pièce occupe toute la case (ou presque)
    # On prend 90% de la case pour laisser un petit padding
    width = (CELL_SIZE * 0.9) / image_size
    height = (CELL_SIZE * 0.9) / image_size
    
    return x_center, y_center, width, height

def generate_yolo_annotation(board_state, output_path):
    """
    Génère un fichier .txt YOLO pour une position donnée.
    Format : une ligne par pièce
        class_id x_center y_center width height
    """
    lines = []
    
    for case_str, piece_name in board_state.items():
        case_index = int(case_str)
        
        # Récupérer la classe YOLO
        class_id = PIECE_TO_CLASS.get(piece_name)
        if class_id is None:
            print(f"  ⚠️ Pièce inconnue : {piece_name}")
            continue
        
        # Calculer la bounding box
        x_center, y_center, width, height = case_to_yolo_bbox(case_index)
        
        # Format YOLO : 6 décimales pour la précision
        line = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
        lines.append(line)
    
    # Écrire le fichier
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return len(lines)

def generate_classes_file():
    """Génère le fichier classes.txt et data.yaml pour YOLOv8."""
    # Fichier classes.txt (pour Roboflow / autres)
    classes_path = os.path.join(LABELS_DIR, "classes.txt")
    with open(classes_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(CLASS_NAMES))
    print(f"✅ classes.txt généré : {classes_path}")
    
    # Fichier data.yaml (pour YOLOv8 / Ultralytics)
    yaml_path = r"C:\ludii\output\data.yaml"
    yaml_content = f"""# Dataset Chess généré depuis Ludii
path: C:/ludii/output
train: images
val: images
test: images

nc: {len(CLASS_NAMES)}
names: {CLASS_NAMES}
"""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    print(f"✅ data.yaml généré : {yaml_path}")

# === SCRIPT PRINCIPAL ===
print("=" * 60)
print("Génération des annotations YOLO depuis les positions")
print("=" * 60)

with open(INPUT_JSON, 'r', encoding='utf-8') as f:
    positions = json.load(f)

print(f"📥 {len(positions)} positions à annoter\n")

total_annotations = 0

for i, pos in enumerate(positions):
    move_num = pos["move_number"]
    board_state = pos["board"]
    
    filename = f"chess_position_{move_num:03d}.txt"
    output_path = os.path.join(LABELS_DIR, filename)
    
    num_annotations = generate_yolo_annotation(board_state, output_path)
    total_annotations += num_annotations
    
    print(f"  ✅ {filename} ({num_annotations} bounding boxes)")

# Générer le fichier des classes
print()
generate_classes_file()

print(f"\n✅ Annotations générées :")
print(f"   📁 {LABELS_DIR}")
print(f"   📊 Total bounding boxes : {total_annotations}")
print(f"   📊 Moyenne par image : {total_annotations / len(positions):.1f}")