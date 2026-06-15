import torch
import sys
from pathlib import Path

HEIGHT = 5
WIDTH = 5
NUM_COLORS = 4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importe ton modèle (ajuste les dimensions si besoin)
from Model import GraphColoringNet 

# 1. Instancier le modèle "vide"
model = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=NUM_COLORS)

# 2. Charger ton cerveau entraîné
checkpoint = torch.load("checkpoints/Alice/latest.pt", map_location="cpu")
model.load_state_dict(checkpoint["model_state_dict"])
model.eval() # Mode évaluation

# 3. Créer une "fausse" observation (1 grille, 4 couleurs, 5 de haut, 5 de large)
dummy_input = torch.randn(1, NUM_COLORS+1, HEIGHT, WIDTH)
# 4. Exporter le plan de construction en format universel ONNX
torch.onnx.export(
    model, 
    dummy_input, 
    "alice_brain" + str(WIDTH) + "x" + str(HEIGHT) + ".onnx",
    input_names=["Observation_Grille"],
    output_names=["Logits_Actor", "Value_Critic"]
)

print("Modèle exporté avec succès : alice_brain" + str(WIDTH) + "x" + str(HEIGHT) + ".onnx")