import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import yaml
import argparse
import os
import pandas as pd
from tqdm import tqdm
import numpy as np

from src.core.model.chess_net import ChessNet
from src.core.model.dataset import ChessDataset
from src.core.data.features import move_to_index

def compare_models(config_path, checkpoints):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    dataset = ChessDataset(config["dataset_path"])
    eval_size = min(2000, len(dataset))
    _, val_ds = torch.utils.data.random_split(dataset, [len(dataset) - eval_size, eval_size])
    val_loader = DataLoader(val_ds, batch_size=256, num_workers=0)
    
    results = []
    
    for name, cp_path in checkpoints.items():
        if not os.path.exists(cp_path):
            print(f"Skipping {name}, checkpoint not found at {cp_path}")
            continue
            
        print(f"Evaluating {name}...")
        
        model = ChessNet(
            channels=config.get("channels", 64),
            num_res_blocks=config.get("num_res_blocks", 4),
            use_value_head=config.get("use_value_head", False)
        ).to(device)
        
        state_dict = torch.load(cp_path, map_location=device)
        model.load_state_dict(state_dict)
        model.eval()
        
        correct = 0
        top5_correct = 0
        total = 0
        
        with torch.no_grad():
            for boards, moves, _ in tqdm(val_loader, desc=name):
                boards, moves = boards.to(device), moves.to(device)
                logits = model(boards)
                
                preds = logits.argmax(1)
                correct += (preds == moves).sum().item()
                
                top5 = logits.topk(5, dim=1).indices
                top5_correct += (top5 == moves.unsqueeze(1)).any(dim=1).sum().item()
                
                total += boards.size(0)
        
        acc = correct / total
        top5_acc = top5_correct / total
        results.append({
            "Model": name,
            "Accuracy": acc,
            "Top-5 Accuracy": top5_acc,
            "Total Positions": total
        })
    
    df = pd.DataFrame(results)
    print("\nComparison Results:")
    print(df.to_string(index=False))
    
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/model_comparison.csv", index=False)
    print(f"\nResults saved to results/model_comparison.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    
    checkpoints = {
        "Current Best": "checkpoints/best_model.pt",
    }
    
    if os.path.exists("checkpoints"):
        for f in os.listdir("checkpoints"):
            if f.endswith(".pt") and f != "best_model.pt":
                checkpoints[f.replace(".pt", "")] = os.path.join("checkpoints", f)
                
    # checkpoints["Maia-1100"] = "checkpoints/maia/maia-1100.pt"

    compare_models(args.config, checkpoints)
