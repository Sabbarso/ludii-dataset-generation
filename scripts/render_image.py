import json
import os
from PIL import Image, ImageDraw, ImageFont

# === CHEMINS ===
INPUT_JSON = r"C:\ludii\output\chess_positions.json"
OUTPUT_DIR = r"C:\ludii\output\images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === PARAMÈTRES DE RENDU ===
BOARD_SIZE = 512        # taille totale de l'image en pixels
CELL_SIZE = BOARD_SIZE // 8  # 64 pixels par case
LIGHT_COLOR = (240, 217, 181)  # beige clair
DARK_COLOR = (181, 136, 99)    # marron
PIECE_COLOR_WHITE = (255, 255, 255)
PIECE_COLOR_BLACK = (0, 0, 0)
PIECE_OUTLINE = (50, 50, 50)

# === SYMBOLES UNICODE POUR LES PIÈCES ===
LUDII_TO_SYMBOL = {
    "Pawn1":   "♙", "Rook1":   "♖", "Knight1": "♘",
    "Bishop1": "♗", "Queen1":  "♕", "King1":   "♔",
    "Pawn2":   "♟", "Rook2":   "♜", "Knight2": "♞",
    "Bishop2": "♝", "Queen2":  "♛", "King2":   "♚",
}

# Couleur de chaque pièce (Player 1 = blanc, Player 2 = noir)
LUDII_TO_COLOR = {
    "Pawn1":   "white", "Rook1":   "white", "Knight1": "white",
    "Bishop1": "white", "Queen1":  "white", "King1":   "white",
    "Pawn2":   "black", "Rook2":   "black", "Knight2": "black",
    "Bishop2": "black", "Queen2":  "black", "King2":   "black",
}

# Lettre représentant la pièce (pour le fallback texte)
LUDII_TO_LETTER = {
    "Pawn1":   "P", "Rook1":   "R", "Knight1": "N",
    "Bishop1": "B", "Queen1":  "Q", "King1":   "K",
    "Pawn2":   "p", "Rook2":   "r", "Knight2": "n",
    "Bishop2": "b", "Queen2":  "q", "King2":   "k",
}

def case_to_pixel(case_index):
    """
    Convertit l'index de case Ludii (0-63) en coordonnées pixel (x, y).
    Case 0 = a1 = en bas à gauche.
    Case 63 = h8 = en haut à droite.
    """
    col = case_index % 8           # colonne 0-7
    row = case_index // 8          # rangée 0-7 (0 = bas)
    
    # En image, y=0 est en haut, donc on inverse la rangée
    pixel_x = col * CELL_SIZE
    pixel_y = (7 - row) * CELL_SIZE
    
    return pixel_x, pixel_y

def draw_board(draw):
    """Dessine les 64 cases du plateau (alternance couleurs)."""
    for row in range(8):
        for col in range(8):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            # Couleur alternée
            color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
            draw.rectangle(
                [x, y, x + CELL_SIZE, y + CELL_SIZE],
                fill=color
            )

def get_font(size):
    """Essaye de charger une police qui supporte les symboles Unicode."""
    fonts_to_try = [
        "C:\\Windows\\Fonts\\seguisym.ttf",     # Segoe UI Symbol
        "C:\\Windows\\Fonts\\arial.ttf",         # Arial
        "C:\\Windows\\Fonts\\DejaVuSans.ttf",    # DejaVu
    ]
    for font_path in fonts_to_try:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    return ImageFont.load_default()

def draw_piece(draw, case_index, piece_name, font):
    """Dessine une pièce sur la case spécifiée."""
    x, y = case_to_pixel(case_index)
    
    symbol = LUDII_TO_SYMBOL.get(piece_name, "?")
    color = LUDII_TO_COLOR.get(piece_name, "white")
    
    # Position centrée dans la case
    text_color = PIECE_COLOR_WHITE if color == "white" else PIECE_COLOR_BLACK
    outline_color = PIECE_OUTLINE
    
    # Centrer le symbole dans la case
    bbox = draw.textbbox((0, 0), symbol, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = x + (CELL_SIZE - text_width) // 2 - bbox[0]
    text_y = y + (CELL_SIZE - text_height) // 2 - bbox[1]
    
    # Dessiner avec contour pour bonne visibilité
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        draw.text((text_x + dx, text_y + dy), symbol, font=font, fill=outline_color)
    draw.text((text_x, text_y), symbol, font=font, fill=text_color)

def render_position(board_state, output_path):
    """Génère l'image complète d'une position."""
    img = Image.new("RGB", (BOARD_SIZE, BOARD_SIZE), "white")
    draw = ImageDraw.Draw(img)
    
    # 1. Dessiner le plateau
    draw_board(draw)
    
    # 2. Charger la police pour les pièces
    font = get_font(int(CELL_SIZE * 0.85))
    
    # 3. Dessiner chaque pièce
    for case_str, piece_name in board_state.items():
        case_index = int(case_str)
        draw_piece(draw, case_index, piece_name, font)
    
    # 4. Sauvegarder
    img.save(output_path)

# === SCRIPT PRINCIPAL ===
print("=" * 60)
print("Génération des images depuis les positions Ludii")
print("=" * 60)

with open(INPUT_JSON, 'r', encoding='utf-8') as f:
    positions = json.load(f)

print(f"📥 {len(positions)} positions à traiter\n")

for i, pos in enumerate(positions):
    move_num = pos["move_number"]
    board_state = pos["board"]
    
    filename = f"chess_position_{move_num:03d}.png"
    output_path = os.path.join(OUTPUT_DIR, filename)
    render_position(board_state, output_path)
    
    print(f"  ✅ {filename} ({len(board_state)} pièces)")

print(f"\n✅ {len(positions)} images générées dans :")
print(f"   {OUTPUT_DIR}")