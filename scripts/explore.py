import jpype
import jpype.imports
from jpype import JClass

# Chemin vers le .jar Ludii
LUDII_JAR_PATH = r"C:\ludii\Ludii-1.3.14.jar"

# Démarrer la JVM
if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[LUDII_JAR_PATH])
    print("✅ JVM démarrée avec Ludii.jar")

# Le bon chemin trouvé par exploration : other.GameLoader
try:
    GameLoader = JClass("other.GameLoader")
    print("✅ GameLoader trouvé dans le package 'other'")
except Exception as e:
    print(f"❌ GameLoader non trouvé : {e}")

# Charger le jeu Chess
try:
    game = GameLoader.loadGameFromName("Chess.lud")
    if game is not None:
        print(f"✅ Jeu chargé : {game.name()}")
        print(f"   Nombre de joueurs : {game.players().count()}")
        # Quelques infos sur le plateau
        board = game.board()
        print(f"   Type de plateau : {board.getClass().getSimpleName()}")
    else:
        print("❌ Le jeu retourné est null")
except Exception as e:
    print(f"❌ Erreur de chargement : {e}")

# Arrêter la JVM proprement
jpype.shutdownJVM()
print("✅ Test terminé")