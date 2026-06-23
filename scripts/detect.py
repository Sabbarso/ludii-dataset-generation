import jpype
from jpype import JClass

LUDII_JAR_PATH = r"C:\ludii\Ludii-1.3.14.jar"

if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[LUDII_JAR_PATH])

GameLoader = JClass("other.GameLoader")
Trial = JClass("other.trial.Trial")
Context = JClass("other.context.Context")

GAMES = [
    "Chess.lud",
    "Half Chess.lud",
    "Los Alamos Chess.lud",
    "Symmetric Chess.lud",
    "Double Chess.lud",
]

print("=" * 70)
print("Détection des dimensions exactes de chaque plateau")
print("=" * 70)

for game_name in GAMES:
    print(f"\n🔍 {game_name}")
    print("-" * 70)
    
    game = GameLoader.loadGameFromName(game_name)
    if game is None:
        print("  ❌ Non chargé")
        continue
    
    trial = Trial(game)
    context = Context(game, trial)
    game.start(context)
    
    topology = game.board().topology()
    num_cells = topology.cells().size()
    
    # Méthode 1 : récupérer les coordonnées de chaque case
    print(f"  📐 Nombre total de cases : {num_cells}")
    
    # Récupérer les positions x,y de chaque case pour déduire les dimensions
    try:
        cells = topology.cells()
        x_coords = set()
        y_coords = set()
        
        for i in range(num_cells):
            cell = cells.get(i)
            # Chaque cellule a une position centroïde
            center = cell.centroid()
            # Position 3D, on prend x et y
            x = float(center.getX())
            y = float(center.getY())
            x_coords.add(round(x, 2))
            y_coords.add(round(y, 2))
        
        cols = len(x_coords)
        rows = len(y_coords)
        
        print(f"  📊 Dimensions détectées : {cols} colonnes × {rows} rangées")
        print(f"  ✅ Vérification : {cols * rows} = {num_cells} ? {'OUI' if cols * rows == num_cells else 'NON'}")
        
        # Afficher les coordonnées uniques (utile pour debug)
        x_sorted = sorted(x_coords)
        y_sorted = sorted(y_coords)
        print(f"  📍 X (colonnes) : min={x_sorted[0]:.2f}, max={x_sorted[-1]:.2f}")
        print(f"  📍 Y (rangées) : min={y_sorted[0]:.2f}, max={y_sorted[-1]:.2f}")
        
    except Exception as e:
        print(f"  ⚠️ Impossible de détecter les dimensions : {str(e)[:80]}")
    
    # Position initiale - distribution des pièces
    container_state = context.state().containerStates()[0]
    pieces_by_row = {}
    
    components = game.equipment().components()
    
    for cell_idx in range(num_cells):
        piece_id = container_state.whatCell(cell_idx)
        if piece_id > 0:
            try:
                cell = cells.get(cell_idx)
                y = round(float(cell.centroid().getY()), 2)
                pieces_by_row[y] = pieces_by_row.get(y, 0) + 1
            except:
                pass
    
    if pieces_by_row:
        print(f"  🎯 Distribution initiale (pièces par rangée Y) :")
        for y in sorted(pieces_by_row.keys()):
            print(f"      Y={y}: {pieces_by_row[y]} pièces")

jpype.shutdownJVM()
print("\n✅ Détection terminée")