import jpype
from jpype import JClass
import random

LUDII_JAR_PATH = r"C:\ludii\Ludii-1.3.14.jar"

# Démarrer la JVM
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[LUDII_JAR_PATH])
    print("✅ JVM démarrée")

# Charger les classes Ludii avec les bons chemins trouvés
GameLoader = JClass("other.GameLoader")
Trial = JClass("other.trial.Trial")
Context = JClass("other.context.Context")

# Charger Chess
game = GameLoader.loadGameFromName("Chess.lud")
print(f"✅ Jeu chargé : {game.name()}")

# Créer un Trial (= une partie) et un Context (= état de jeu)
trial = Trial(game)
context = Context(game, trial)

# Démarrer la partie
game.start(context)
print("✅ Partie démarrée (position initiale)")

# Jouer des coups aléatoires (max 50 pour le test)
max_moves = 50
move_count = 0

print("\n--- Déroulement de la partie ---")

while not trial.over() and move_count < max_moves:
    # Obtenir tous les coups légaux pour la position actuelle
    legal_moves = game.moves(context).moves()
    
    if legal_moves.size() == 0:
        print("Aucun coup légal disponible. Fin.")
        break
    
    # Choisir un coup aléatoire
    move_index = random.randint(0, legal_moves.size() - 1)
    chosen_move = legal_moves.get(move_index)
    
    # Appliquer le coup
    game.apply(context, chosen_move)
    move_count += 1
    
    print(f"  Coup {move_count}: {chosen_move.toString()}")

print(f"\n✅ Partie terminée après {move_count} coups")
print(f"   Trial.over() = {trial.over()}")

# Arrêter la JVM
jpype.shutdownJVM()
print("✅ Script terminé")