import h5py
import torch
import numpy as np
from torch.utils.data import Dataset

class ChessDataset(Dataset):
    def __init__(self, hdf5_path: str):
        self.hdf5_path = hdf5_path
        
        # The dataset is small enough (~120MB) to load entirely into RAM
        # This completely removes the I/O bottleneck and makes training super fast
        with h5py.File(self.hdf5_path, "r") as f:
            # Pre-load as torch tensors
            self.boards = torch.tensor(f["boards"][:], dtype=torch.float32)
            self.moves = torch.tensor(f["moves"][:], dtype=torch.long)
            self.results = torch.tensor(f["results"][:], dtype=torch.float32)
            self.length = len(self.moves)
            
    def __len__(self):
        return self.length
    
    def __getitem__(self, idx):
        return self.boards[idx], self.moves[idx], self.results[idx]

