import os

MERGED_DIR = r"C:\ludii\output_dataset\merged"

print("=" * 70)
print("VÉRIFICATION DU DATASET MERGED")
print("=" * 70)

splits = ["train", "val", "test"]
total_images = 0
total_labels = 0

for split in splits:
    images_dir = os.path.join(MERGED_DIR, "images", split)
    labels_dir = os.path.join(MERGED_DIR, "labels", split)
    
    if not os.path.exists(images_dir):
        print(f"❌ Dossier manquant : {images_dir}")
        continue
    
    images = [f for f in os.listdir(images_dir) if f.endswith(".png")]
    labels = [f for f in os.listdir(labels_dir) if f.endswith(".txt")]
    
    total_images += len(images)
    total_labels += len(labels)
    
    print(f"\n📁 {split.upper()}")
    print(f"   Images  : {len(images)} fichiers .png")
    print(f"   Labels  : {len(labels)} fichiers .txt")
    
    # Vérifier que chaque image a son annotation
    image_bases = {f.replace(".png", "") for f in images}
    label_bases = {f.replace(".txt", "") for f in labels}
    
    missing_labels = image_bases - label_bases
    missing_images = label_bases - image_bases
    
    if missing_labels:
        print(f"   ⚠️ {len(missing_labels)} images sans label !")
    if missing_images:
        print(f"   ⚠️ {len(missing_images)} labels sans image !")
    if not missing_labels and not missing_images:
        print(f"   ✅ Correspondance parfaite image ↔ label")
    
    # Compter le nombre total d'annotations (lignes)
    total_boxes = 0
    for lbl_file in labels[:100]:  # échantillon de 100
        with open(os.path.join(labels_dir, lbl_file), 'r') as f:
            total_boxes += len(f.readlines())
    
    avg_boxes = total_boxes / min(100, len(labels)) if labels else 0
    print(f"   📊 Moyenne bounding boxes par image : {avg_boxes:.1f}")

# Vérifier data.yaml
yaml_path = os.path.join(MERGED_DIR, "data.yaml")
if os.path.exists(yaml_path):
    print(f"\n✅ data.yaml présent : {yaml_path}")
    with open(yaml_path, 'r') as f:
        print(f.read())
else:
    print(f"\n❌ data.yaml MANQUANT !")

print("=" * 70)
print(f"📊 TOTAL : {total_images} images | {total_labels} annotations")
print("=" * 70)

if total_images == total_labels:
    print("\n✅ DATASET PARFAITEMENT ANNOTÉ — Prêt pour YOLOv8 !")
else:
    print(f"\n⚠️ Différence : {abs(total_images - total_labels)} fichiers manquants")