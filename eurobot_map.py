import numpy as np
from PIL import Image, ImageDraw

# --- CONFIGURATION DU TERRAIN ---
# Dimensions en mm (10mm = 1 pixel pour une résolution de 0.01m/px)
WIDTH_MM = 3000
HEIGHT_MM = 2000
RES = 10 # 10mm par pixel
BORDER_THICKNESS = 10 // RES

# Couleurs ROS (0 = Obstacle/Noir, 255 = Libre/Blanc, 200 = Zone d'intérêt/Gris clair)
BLACK = 0
WHITE = 255
GREY_ZONE = 210  # Pour que le robot puisse rouler dessus mais qu'on les voie

def create_map():
    # Création de l'image de base (tout est libre au départ)
    img_w, img_h = WIDTH_MM // RES, HEIGHT_MM // RES
    image = Image.new('L', (img_w, img_h), WHITE)
    draw = ImageDraw.Draw(image)

    # 1. LE GRENIER (ATTIC) - Zone noire (Obstacle)
    # Situé en haut de la table (environ 450mm de profondeur selon les refs habituelles)
    attic_depth = 450 // RES
    draw.rectangle([60, 0, img_w - 60, attic_depth], fill=BLACK)

    # 2. LES BORDURES - Noir
    # Extérieur de la table
    draw.rectangle([0, 0, img_w-1, img_h-1], outline=BLACK, width=BORDER_THICKNESS)

    # 3. EMPLACEMENT DES BOITES (Boxes) & ZONES VERTES (Reception)
    # On définit les centres approximatifs basés sur le visuel "Winter is Coming"
    # Format: (x_center_mm, y_center_mm)
    box_locations = [
        (1250, 550), (1750, 550),   # Ligne du haut
        (100, 1200), (800, 1200), (1500, 1200), (2200, 1200), (2900, 1200), # Ligne du milieu
        (700, 1900), (1500, 1900), (2300, 1900), # Ligne du bas
    ]
    
    box_size = 150 // RES # Taille d'une boîte env 15x15cm
    green_area_size = 200 // RES # Zone de réception autour

    for (x_mm, y_mm) in box_locations:
        px, py = x_mm // RES, y_mm // RES
        
        # Dessiner la zone verte (Gris clair pour ROS pour ne pas bloquer le robot)
        draw.rectangle([px - green_area_size//2, py - green_area_size//2, 
                        px + green_area_size//2, py + green_area_size//2], 
                       outline=WHITE, fill=GREY_ZONE)
        
        # Dessiner l'emplacement précis de la boîte (Contour noir, fond libre)
        draw.rectangle([px - box_size//2, py - box_size//2, 
                        px + box_size//2, py + box_size//2], 
                       outline=WHITE, fill=WHITE)

    # Sauvegarde de l'image
    image.save("eurobot_2026_map.png")
    print("Image 'eurobot_2026_map.png' générée.")

    # 4. GÉNÉRATION DU FICHIER YAML
    yaml_content = f"""image: eurobot_2026_map.png
resolution: {RES/1000.0}
origin: [{-WIDTH_MM/2000.0}, 0.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""
    with open("eurobot_2026_map.yaml", "w") as f:
        f.write(yaml_content)
    print("Fichier 'eurobot_2026_map.yaml' généré.")

if __name__ == "__main__":
    create_map()