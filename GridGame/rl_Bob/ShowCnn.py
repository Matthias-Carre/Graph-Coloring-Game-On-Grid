import torch
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Ajout du dossier parent au path (comme dans ton code)
sys.path.insert(0, str(Path(__file__).parent.parent))

from Model import GraphColoringNet

def create_trap_observation(width, height, num_colors):
    """
    Crée manuellement l'observation (One-hot) pour ton 'set up' spécifique :
    Une case vide au centre, entourée des couleurs 1, 2 et 3.
    """
    # Initialisation : on met toutes les cases à l'état "vide" (canal 0)
    obs = np.zeros((num_colors + 1, height, width), dtype=np.float32)
    obs[0, :, :] = 1.0 
    
    center_x, center_y = width // 2, height // 2
    
    # On place la Couleur 1 en Haut
    obs[0, center_y - 1, center_x] = 0.0 # N'est plus vide
    obs[1, center_y - 1, center_x] = 1.0 # Est de couleur 1
    
    # On place la Couleur 2 à Gauche
    obs[0, center_y, center_x - 1] = 0.0
    obs[2, center_y, center_x - 1] = 1.0
    
    # On place la Couleur 3 à Droite
    obs[0, center_y, center_x + 1] = 0.0
    obs[3, center_y, center_x + 1] = 1.0
    
    return obs

def matrix_to_obs(matrix, num_colors=4):
    """
    Traduit une matrice 2D (liste de listes) en observation tensorielle (Canaux, H, W).
    0 = vide, 1-4 = couleurs.
    """
    # On s'assure de travailler avec un tableau NumPy
    grid = np.array(matrix)
    height, width = grid.shape
    
    # Création du tenseur vide rempli de zéros
    obs = np.zeros((num_colors + 1, height, width), dtype=np.float32)
    
    # Remplissage : pour chaque case, on met un "1" sur la bonne couche de couleur
    for y in range(height):
        for x in range(width):
            val = grid[y, x]
            obs[val, y, x] = 1.0
            
    return obs


def main():
    WIDTH, HEIGHT, COLORS = 5, 5, 4


    matrice = [[0, 0, 0, 0, 0],
               [0, 0, 3, 0, 0],
               [0, 1, 0, 0, 0],
               [0, 0, 2, 0, 0],
               [0, 0, 0, 0, 0]]
    
    # 1. Création de l'observation et conversion pour PyTorch
    obs_numpy = matrix_to_obs(matrice, COLORS)
    obs_tensor = torch.tensor(obs_numpy).unsqueeze(0) # Ajout de la dimension batch: [1, 5, 5, 5]
    
    # 2. Chargement du cerveau de Bob
    script_dir = Path(__file__).parent.parent
    MODEL_PATH = str(script_dir / "Models" / "Bob4x4.pt")
    
    model = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    try:
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        print("Modèle chargé avec succès. Extraction des Feature Maps...")
    except FileNotFoundError:
        print(f"Fichier {MODEL_PATH} introuvable. Le réseau sera initialisé au hasard (non entraîné).")
    
    # 3. L'EXTRACTION CHIRURGICALE
    # Au lieu de faire model(obs_tensor), on isole la première couche Conv + le ReLU
    # Dans ton init: self.shared_cnn[0] est le Conv2d, self.shared_cnn[1] est le ReLU
    first_conv_layer = model.shared_cnn[0]
    first_relu = model.shared_cnn[1]
    
    with torch.no_grad():
        # On fait passer la donnée uniquement dans ce petit bout du réseau
        raw_features = first_conv_layer(obs_tensor)
        activated_features = first_relu(raw_features)
        
    # On retire la dimension batch pour l'affichage : la shape devient [32, H, W]
    feature_maps = activated_features.squeeze(0).numpy()
    
    # 4. AFFICHAGE DES 32 CARTES DE CHALEUR (Matplotlib)
    fig, axes = plt.subplots(4, 8, figsize=(16, 8))
    fig.suptitle(f"Les 32 Feature Maps de la 1ère couche (Filtres 3x3)", fontsize=16)
    
    # On cherche la valeur d'activation maximale globale pour normaliser les couleurs
    vmax = np.max(feature_maps)
    
    for i, ax in enumerate(axes.flat):
        # On extrait la grille 2D du canal i
        fmap = feature_maps[i]
        
        # Affichage avec une "carte de chaleur" (colormap 'magma' ou 'hot')
        im = ax.imshow(fmap, cmap='magma', vmin=0, vmax=vmax)
        ax.set_title(f"Filtre {i}")
        ax.axis('off') # On cache les axes X et Y pour plus de clarté
        
    # Ajout d'une barre de légende pour les couleurs
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    fig.colorbar(im, cax=cbar_ax, label="Niveau d'activation (Signal)")
    
    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()

if __name__ == "__main__":
    main()