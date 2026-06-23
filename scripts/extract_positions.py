import jpype
from jpype import JClass
import random
import json

LUDII_JAR_PATH = r"C:\ludii\Ludii-1.3.14.jar"

# Démarrer la JVM
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[LUDII_JAR_PATH])
    print("✅ JVM démarrée")

# Charger les classes Ludii
GameLoader = JClass("other.GameLoader")
Trial = JClass("other.trial.Trial")
Context = JClass("other.context.Context")

# Charger Chess
game = GameLoader.loadGameFromName("Chess.lud")
print(f"✅ Jeu chargé : {game.name()}")

# Créer Trial et Context
trial = Trial(game)
context = Context(game, trial)
game.start(context)

# Récupérer les composants (types de pièces) du jeu
components = game.equipment().components()
print(f"\n📋 Pièces du jeu ({components.length - 1} types) :")
piece_map = {}
for i in range(1, components.length):  # index 0 = vide, on commence à 1
    comp = components[i]
    if comp is not None:
        name = str(comp.name())
        owner = comp.owner()
        piece_map[i] = name
        print(f"  ID {i:2d} → {name} (joueur {owner})")

# Fonction pour extraire l'état actuel du plateau
def get_board_state(context):
    """
    Retourne un dictionnaire {case: pièce}
    Case = index (0-63 pour échiquier)
    Pièce = nom de la pièce (ou None si vide)
    """
    state = context.state()
    container_state = state.containerStates()[0]  # plateau principal
    
    board_state = {}
    # Pour chaque case du plateau
    num_cells = game.board().topology().cells().size()
    
    for cell_index in range(num_cells):
        # whatCell(cell) retourne l'ID de la pièce sur cette case (0 si vide)
        piece_id = container_state.whatCell(cell_index)
        if piece_id > 0:
            board_state[cell_index] = piece_map.get(piece_id, f"Unknown({piece_id})")
    
    return board_state

# === Position initiale ===
print("\n" + "=" * 60)
print("Position INITIALE")
print("=" * 60)
initial = get_board_state(context)
print(f"Nombre de pièces : {len(initial)}")
for case, piece in sorted(initial.items()):
    print(f"  Case {case:2d} : {piece}")

# === Jouer la partie et capturer les positions ===
positions = []
positions.append({
    "move_number": 0,
    "board": initial
})

max_moves = 20  # on en fait moins pour le test, et on affiche
move_count = 0

print("\n" + "=" * 60)
print(f"Simulation de {max_moves} coups")
print("=" * 60)

while not trial.over() and move_count < max_moves:
    legal_moves = game.moves(context).moves()
    if legal_moves.size() == 0:
        break
    
    chosen_move = legal_moves.get(random.randint(0, legal_moves.size() - 1))
    game.apply(context, chosen_move)
    move_count += 1
    
    # Capturer l'état du plateau après ce coup
    current_state = get_board_state(context)
    positions.append({
        "move_number": move_count,
        "board": current_state
    })
    
    print(f"  Coup {move_count:2d} → {len(current_state)} pièces sur le plateau")

# === Afficher la position finale ===
print("\n" + "=" * 60)
print(f"Position FINALE (après {move_count} coups)")
print("=" * 60)
final = positions[-1]["board"]
print(f"Nombre de pièces : {len(final)}")
for case, piece in sorted(final.items()):
    print(f"  Case {case:2d} : {piece}")

# === Sauvegarder en JSON ===
output_file = r"C:\ludii\output\chess_positions.json"
import os
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(positions, f, indent=2)

print(f"\n✅ {len(positions)} positions sauvegardées dans :")
print(f"   {output_file}")

jpype.shutdownJVM()
print("✅ Script terminé")