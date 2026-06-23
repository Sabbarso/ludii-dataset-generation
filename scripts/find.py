import zipfile

LUDII_JAR_PATH = r"C:\ludii\Ludii-1.3.14.jar"

# Classes qu'on cherche
to_find = ["Trial", "Context", "RandomProvider", "RandomProviderDefaultState"]

with zipfile.ZipFile(LUDII_JAR_PATH, 'r') as jar:
    names = jar.namelist()
    
    for cls in to_find:
        print(f"\n=== Recherche de '{cls}' ===")
        found = False
        for n in names:
            # Chercher le fichier exact (pas les sous-classes $)
            if n.endswith(f'/{cls}.class') or n == f'{cls}.class':
                # Éviter les classes internes (qui contiennent $)
                if '$' not in n:
                    print(f"  ✅ {n}")
                    found = True
        if not found:
            print(f"  ❌ Non trouvé directement, recherche élargie...")
            for n in names:
                if cls in n and n.endswith('.class') and '$' not in n:
                    print(f"     {n}")