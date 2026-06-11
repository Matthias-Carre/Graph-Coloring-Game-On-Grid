import torch
import torchrl
import numpy as np
import gymnasium as gym
import sys

print(f"Système d'exploitation : {sys.platform}")
print(f"Version de Python      : {sys.version.split()[0]}")
print("-" * 40)
print(f"PyTorch                : {torch.__version__}")
print(f"TorchRL                : {torchrl.__version__}")
print(f"NumPy                  : {np.__version__}")
print(f"Gymnasium              : {gym.__version__}")