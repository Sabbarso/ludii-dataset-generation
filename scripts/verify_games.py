import jpype
from jpype import JClass

LUDII_JAR_PATH = r"C:\ludii\Ludii-1.3.14.jar"

# Démarrer la JVM
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[LUDII_JAR_PATH])
    print("✅ JVM démarrée\n")

# Charger les classes nécessaires
GameLoader = JClass("other.GameLoader")
Trial = JClass("other.trial.Trial")
Context = JClass("other.context.Context")

# Les 10 jeux à vérifier
GAMES_TO_CHECK = [
    "Chess.lud",
    "Half Chess.lud",
    "Los Alamos Chess.lud",
    "Symmetric Chess.lud",
    "Double Chess.lud",
    "Almost Chess.lud",
    "Pocket Knight Chess.lud",
    "Chess960.lud",
    "Knightmate.lud",
    "Progressive Chess.lud",
]

# Mapping des pièces standard (12 classes attendues)
STANDARD_PIECES = {
    "King1", "Queen1", "Rook1", "Bishop1", "Knight1", "Pawn1",
    "King2", "Queen2", "Rook2", "Bishop2", "Knight2", "Pawn2"
}

print("=" * 75)
print("VÉRIFICATION DES 10 JEUX CHESS DANS LUDII")
print("=" * 75)

available = []      # ✅ Jeux compatibles avec notre pipeline
non_standard = []   # ⚠️ Jeux avec pièces spéciales
not_found = []      # ❌ Jeux non trouvés

for game_name in GAMES_TO_CHECK:
    print(f"\n🔍 Test : {game_name}")
    print("-" * 75)
    
    try:
        # Charger le jeu
        game = GameLoader.loadGameFromName(game_name)
        
        if game is None:
            print(f"  ❌ Jeu non trouvé (null)")
            not_found.append(game_name)
            continue
        
        # Informations de base
        actual_name = str(game.name())
        num_players = game.players().count()
        
        # Dimensions du plateau
        topology = game.board().topology()
        num_cells = topology.cells().size()
        
        # Essayer d'obtenir les dimensions précises (rows × cols)
        try:
            # Pour un plateau rectangulaire standard
            board_obj = game.board()
            num_rows = board_obj.numSites()  # peut varier selon la version
        except:
            num_rows = None
        
        # Pièces du jeu
        components = game.equipment().components()
        pieces = []
        for i in range(1, components.length):
            comp = components[i]
            if comp is not None:
                pieces.append(str(comp.name()))
        
        # Détecter si toutes les pièces sont standard
        pieces_set = set(pieces)
        non_standard_pieces = pieces_set - STANDARD_PIECES
        missing_pieces = STANDARD_PIECES - pieces_set
        
        # Démarrer une partie pour valider
        trial = Trial(game)
        context = Context(game, trial)
        game.start(context)
        
        # Comptage des pièces sur le plateau initial
        container_state = context.state().containerStates()[0]
        initial_pieces = 0
        for cell_idx in range(num_cells):
            if container_state.whatCell(cell_idx) > 0:
                initial_pieces += 1
        
        # Affichage
        print(f"  ✅ Chargé : {actual_name}")
        print(f"  👥 Joueurs : {num_players}")
        print(f"  📐 Cases : {num_cells}")
        print(f"  🎯 Pièces sur position initiale : {initial_pieces}")
        print(f"  🎨 Types de pièces ({len(pieces)}) : {pieces}")
        
        if non_standard_pieces:
            print(f"  ⚠️ Pièces non-standard détectées : {non_standard_pieces}")
            non_standard.append((game_name, list(non_standard_pieces)))
        else:
            print(f"  ✅ COMPATIBLE — Toutes les pièces sont standard")
            available.append({
                "name": game_name,
                "actual_name": actual_name,
                "num_cells": num_cells,
                "initial_pieces": initial_pieces,
                "pieces": pieces
            })
    
    except Exception as e:
        print(f"  ❌ ERREUR : {str(e)[:100]}")
        not_found.append(game_name)

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================
print("\n\n" + "=" * 75)
print("RÉSUMÉ FINAL")
print("=" * 75)

print(f"\n✅ JEUX COMPATIBLES ({len(available)}) :")
for g in available:
    # Calcul des dimensions probables (carré ou rectangle)
    n = g["num_cells"]
    # Tester si c'est un carré parfait
    import math
    sqrt_n = int(math.sqrt(n))
    if sqrt_n * sqrt_n == n:
        dim = f"{sqrt_n}×{sqrt_n}"
    elif n == 32:
        dim = "4×8 ou 8×4"
    elif n == 128:
        dim = "16×8 ou 8×16"
    else:
        dim = f"{n} cases"
    
    print(f"  • {g['name']:<30} | {dim:<10} | {g['initial_pieces']} pièces")

if non_standard:
    print(f"\n⚠️  JEUX AVEC PIÈCES NON-STANDARD ({len(non_standard)}) :")
    for game_name, weird_pieces in non_standard:
        print(f"  • {game_name:<30} | Pièces spéciales : {weird_pieces}")

if not_found:
    print(f"\n❌ JEUX NON TROUVÉS ({len(not_found)}) :")
    for g in not_found:
        print(f"  • {g}")

print(f"\n📊 Total : {len(available)} compatibles | {len(non_standard)} non-standard | {len(not_found)} non trouvés")

# Sauvegarder la liste des jeux compatibles pour le script suivant
import json
import os

output_file = r"C:\ludii\output\available_games.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(available, f, indent=2)

print(f"\n💾 Liste des jeux compatibles sauvegardée dans :")
print(f"   {output_file}")

jpype.shutdownJVM()
print("\n✅ Vérification terminée")