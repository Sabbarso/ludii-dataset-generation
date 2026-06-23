"""
Script maître : Génération automatique du dataset YOLO multi-jeux Chess
À partir de Ludii Games via JPype.
"""

import jpype
from jpype import JClass
import random
import os
import json
import shutil
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# ============================================================================
# CONFIGURATION (modifiable selon vos besoins)
# ============================================================================

LUDII_JAR_PATH = r"C:\ludii\Ludii-1.3.14.jar"
OUTPUT_BASE = r"C:\ludii\output_dataset"

# Jeux à traiter (vérifiés disponibles)
GAMES_CONFIG = [
    {"name": "Chess.lud",            "folder": "chess",           "cols": 8,  "rows": 8},
    {"name": "Half Chess.lud",       "folder": "half_chess",      "cols": 8,  "rows": 4},
    {"name": "Los Alamos Chess.lud", "folder": "los_alamos",      "cols": 6,  "rows": 6},
    {"name": "Symmetric Chess.lud",  "folder": "symmetric_chess", "cols": 9,  "rows": 8},
    {"name": "Double Chess.lud",     "folder": "double_chess",    "cols": 16, "rows": 12},
]

# Paramètres de génération
NUM_GAMES_PER_VARIANT = 20      # Nombre de parties par jeu
MAX_MOVES_PER_GAME = 30          # Nombre de coups max par partie
IMAGE_SIZE = 512                 # Taille de l'image en pixels
RANDOM_SEED = 42                 # Pour reproductibilité

# Split train/val/test
TRAIN_RATIO = 0.80
VAL_RATIO = 0.15
TEST_RATIO = 0.05

# ============================================================================
# CLASSES YOLO (12 classes universelles)
# ============================================================================

PIECE_TO_CLASS = {
    "King1": 0, "Queen1": 1, "Rook1": 2,
    "Bishop1": 3, "Knight1": 4, "Pawn1": 5,
    "King2": 6, "Queen2": 7, "Rook2": 8,
    "Bishop2": 9, "Knight2": 10, "Pawn2": 11,
}

CLASS_NAMES = [
    "white_king", "white_queen", "white_rook", "white_bishop",
    "white_knight", "white_pawn",
    "black_king", "black_queen", "black_rook", "black_bishop",
    "black_knight", "black_pawn"
]

PIECE_TO_SYMBOL = {
    "Pawn1":   "♙", "Rook1":   "♖", "Knight1": "♘",
    "Bishop1": "♗", "Queen1":  "♕", "King1":   "♔",
    "Pawn2":   "♟", "Rook2":   "♜", "Knight2": "♞",
    "Bishop2": "♝", "Queen2":  "♛", "King2":   "♚",
}

PIECE_COLOR = {
    "Pawn1": "white", "Rook1": "white", "Knight1": "white",
    "Bishop1": "white", "Queen1": "white", "King1": "white",
    "Pawn2": "black", "Rook2": "black", "Knight2": "black",
    "Bishop2": "black", "Queen2": "black", "King2": "black",
}

# Couleurs visuelles
LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)
OUTLINE = (50, 50, 50)

# ============================================================================
# INITIALISATION JVM
# ============================================================================

print("=" * 75)
print("🎯 GÉNÉRATION DU DATASET CHESS — 5 JEUX")
print("=" * 75)

random.seed(RANDOM_SEED)

if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[LUDII_JAR_PATH])
    print("✅ JVM démarrée\n")

GameLoader = JClass("other.GameLoader")
Trial = JClass("other.trial.Trial")
Context = JClass("other.context.Context")

# ============================================================================
# FONCTIONS DE RENDU
# ============================================================================

def get_font(size):
    """Charger une police supportant les symboles d'échecs Unicode."""
    fonts = [
        "C:\\Windows\\Fonts\\seguisym.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for f in fonts:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except:
                continue
    return ImageFont.load_default()

def render_position(board_state, cols, rows, output_path):
    """Génère une image PNG adaptée aux dimensions du plateau."""
    # Calculer la taille d'une case (le plateau remplit IMAGE_SIZE)
    cell_size = min(IMAGE_SIZE // cols, IMAGE_SIZE // rows)
    
    # Dimensions exactes du plateau
    board_w = cell_size * cols
    board_h = cell_size * rows
    
    # Créer l'image (le plateau est centré dans IMAGE_SIZE × IMAGE_SIZE)
    img = Image.new("RGB", (board_w, board_h), "white")
    draw = ImageDraw.Draw(img)
    
    # Dessiner les cases (alternance couleurs)
    for row in range(rows):
        for col in range(cols):
            x = col * cell_size
            y = row * cell_size
            color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
            draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color)
    
    # Charger la police adaptée à la taille des cases
    font = get_font(int(cell_size * 0.85))
    
    # Dessiner chaque pièce
    for (col, row), piece_name in board_state.items():
        symbol = PIECE_TO_SYMBOL.get(piece_name)
        if symbol is None:
            continue
        
        color = PIECE_COLOR.get(piece_name, "white")
        text_color = (255, 255, 255) if color == "white" else (0, 0, 0)
        
        # Position pixel (col, row) → coin haut-gauche de la case
        # Y est inversé : row=0 en BAS dans Ludii, en HAUT dans l'image
        px = col * cell_size
        py = (rows - 1 - row) * cell_size  # inversion verticale
        
        # Centrer le symbole dans la case
        bbox = draw.textbbox((0, 0), symbol, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        text_x = px + (cell_size - tw) // 2 - bbox[0]
        text_y = py + (cell_size - th) // 2 - bbox[1]
        
        # Dessiner avec contour pour visibilité
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            draw.text((text_x + dx, text_y + dy), symbol, font=font, fill=OUTLINE)
        draw.text((text_x, text_y), symbol, font=font, fill=text_color)
    
    img.save(output_path)
    return board_w, board_h

def generate_yolo_annotation(board_state, cols, rows, img_w, img_h, output_path):
    """Génère le fichier .txt d'annotations YOLO pour une position."""
    cell_size = min(IMAGE_SIZE // cols, IMAGE_SIZE // rows)
    lines = []
    
    for (col, row), piece_name in board_state.items():
        class_id = PIECE_TO_CLASS.get(piece_name)
        if class_id is None:
            continue
        
        # Position pixel centrale de la case
        px = col * cell_size + cell_size // 2
        py = (rows - 1 - row) * cell_size + cell_size // 2
        
        # Normalisation YOLO (0-1)
        x_center = px / img_w
        y_center = py / img_h
        width = (cell_size * 0.9) / img_w
        height = (cell_size * 0.9) / img_h
        
        lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return len(lines)

# ============================================================================
# EXTRACTION DE LA POSITION DEPUIS LUDII
# ============================================================================

def extract_board_state(game, context, cells, piece_id_to_name):
    """
    Retourne un dict {(col, row): piece_name} pour la position actuelle.
    Utilise les coordonnées géométriques (centroïdes) de Ludii.
    """
    container_state = context.state().containerStates()[0]
    num_cells = cells.size()
    state = {}
    
    for cell_idx in range(num_cells):
        piece_id = container_state.whatCell(cell_idx)
        if piece_id > 0:
            piece_name = piece_id_to_name.get(piece_id)
            if piece_name:
                # Coordonnées géométriques
                cell = cells.get(cell_idx)
                center = cell.centroid()
                # X et Y sont au format 0.5, 1.5, 2.5... → on les convertit en entiers
                col = int(float(center.getX()))  # 0.5 → 0, 1.5 → 1, etc.
                row = int(float(center.getY()))
                state[(col, row)] = piece_name
    
    return state

# ============================================================================
# GÉNÉRATION POUR UN JEU
# ============================================================================

def process_game(game_config):
    """Génère le dataset pour un seul jeu."""
    game_name = game_config["name"]
    folder = game_config["folder"]
    cols = game_config["cols"]
    rows = game_config["rows"]
    
    print(f"\n{'='*75}")
    print(f"🎮 {game_name} ({cols}×{rows})")
    print(f"{'='*75}")
    
    # Préparer les dossiers
    game_dir = os.path.join(OUTPUT_BASE, folder)
    images_dir = os.path.join(game_dir, "images")
    labels_dir = os.path.join(game_dir, "labels")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)
    
    # Charger le jeu
    game = GameLoader.loadGameFromName(game_name)
    if game is None:
        print(f"❌ Impossible de charger {game_name}")
        return 0
    
    cells = game.board().topology().cells()
    components = game.equipment().components()
    
    # Mapping piece_id → piece_name pour ce jeu
    piece_id_to_name = {}
    for i in range(1, components.length):
        comp = components[i]
        if comp is not None:
            piece_id_to_name[i] = str(comp.name())
    
    image_count = 0
    
    # Boucler sur N parties
    for game_idx in range(NUM_GAMES_PER_VARIANT):
        trial = Trial(game)
        context = Context(game, trial)
        game.start(context)
        
        # Capturer la position initiale
        state = extract_board_state(game, context, cells, piece_id_to_name)
        
        base_name = f"{folder}_g{game_idx:03d}_m000"
        img_path = os.path.join(images_dir, f"{base_name}.png")
        lbl_path = os.path.join(labels_dir, f"{base_name}.txt")
        
        img_w, img_h = render_position(state, cols, rows, img_path)
        num_boxes = generate_yolo_annotation(state, cols, rows, img_w, img_h, lbl_path)
        image_count += 1
        
        # Jouer des coups
        move_count = 0
        while not trial.over() and move_count < MAX_MOVES_PER_GAME:
            legal_moves = game.moves(context).moves()
            if legal_moves.size() == 0:
                break
            
            chosen_move = legal_moves.get(random.randint(0, legal_moves.size() - 1))
            game.apply(context, chosen_move)
            move_count += 1
            
            # Capturer cette position
            state = extract_board_state(game, context, cells, piece_id_to_name)
            
            base_name = f"{folder}_g{game_idx:03d}_m{move_count:03d}"
            img_path = os.path.join(images_dir, f"{base_name}.png")
            lbl_path = os.path.join(labels_dir, f"{base_name}.txt")
            
            img_w, img_h = render_position(state, cols, rows, img_path)
            generate_yolo_annotation(state, cols, rows, img_w, img_h, lbl_path)
            image_count += 1
        
        if (game_idx + 1) % 5 == 0:
            print(f"  ✅ Partie {game_idx + 1}/{NUM_GAMES_PER_VARIANT} — {image_count} images générées")
    
    print(f"\n📊 Total pour {folder} : {image_count} images")
    return image_count

# ============================================================================
# SPLIT TRAIN/VAL/TEST
# ============================================================================

def create_yolo_split():
    """Mélange toutes les images des 5 jeux et crée le split YOLOv8."""
    print(f"\n{'='*75}")
    print("📦 CRÉATION DU SPLIT TRAIN/VAL/TEST")
    print(f"{'='*75}")
    
    merged_dir = os.path.join(OUTPUT_BASE, "merged")
    
    # Structure YOLOv8
    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(merged_dir, "images", split), exist_ok=True)
        os.makedirs(os.path.join(merged_dir, "labels", split), exist_ok=True)
    
    # Collecter toutes les images
    all_files = []
    for config in GAMES_CONFIG:
        folder = config["folder"]
        images_dir = os.path.join(OUTPUT_BASE, folder, "images")
        if not os.path.exists(images_dir):
            continue
        for fname in os.listdir(images_dir):
            if fname.endswith(".png"):
                base = fname.replace(".png", "")
                img_src = os.path.join(images_dir, fname)
                lbl_src = os.path.join(OUTPUT_BASE, folder, "labels", base + ".txt")
                if os.path.exists(lbl_src):
                    all_files.append((img_src, lbl_src, base))
    
    print(f"📥 Total fichiers à splitter : {len(all_files)}")
    
    # Mélanger aléatoirement
    random.shuffle(all_files)
    
    # Calculer les indices de split
    n = len(all_files)
    train_end = int(n * TRAIN_RATIO)
    val_end = train_end + int(n * VAL_RATIO)
    
    splits = {
        "train": all_files[:train_end],
        "val": all_files[train_end:val_end],
        "test": all_files[val_end:]
    }
    
    # Copier les fichiers
    for split_name, files in splits.items():
        for img_src, lbl_src, base in files:
            img_dst = os.path.join(merged_dir, "images", split_name, base + ".png")
            lbl_dst = os.path.join(merged_dir, "labels", split_name, base + ".txt")
            shutil.copy2(img_src, img_dst)
            shutil.copy2(lbl_src, lbl_dst)
        print(f"  ✅ {split_name}: {len(files)} fichiers")
    
    # Créer data.yaml
    yaml_path = os.path.join(merged_dir, "data.yaml")
    yaml_content = f"""# Dataset Chess multi-jeux généré depuis Ludii
path: {merged_dir.replace(chr(92), '/')}
train: images/train
val: images/val
test: images/test

nc: {len(CLASS_NAMES)}
names: {CLASS_NAMES}
"""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"\n✅ data.yaml créé : {yaml_path}")
    return n

# ============================================================================
# EXÉCUTION PRINCIPALE
# ============================================================================

print(f"📋 Configuration :")
print(f"   • Jeux : {len(GAMES_CONFIG)}")
print(f"   • Parties par jeu : {NUM_GAMES_PER_VARIANT}")
print(f"   • Coups par partie : {MAX_MOVES_PER_GAME}")
print(f"   • Total estimé : ~{len(GAMES_CONFIG) * NUM_GAMES_PER_VARIANT * (MAX_MOVES_PER_GAME + 1)} images")

# Générer pour chaque jeu
totals = {}
for config in GAMES_CONFIG:
    count = process_game(config)
    totals[config["folder"]] = count

# Créer le split final
total_split = create_yolo_split()

# Résumé final
print(f"\n{'='*75}")
print("🎉 GÉNÉRATION TERMINÉE")
print(f"{'='*75}")
print(f"\n📊 Statistiques par jeu :")
for folder, count in totals.items():
    print(f"   • {folder:<25} : {count:5d} images")
print(f"\n📦 Dataset final : {total_split} images dans {OUTPUT_BASE}\\merged\\")
print(f"   • Prêt pour YOLOv8 (data.yaml inclus)")

jpype.shutdownJVM()
print(f"\n✅ Pipeline complet exécuté avec succès")