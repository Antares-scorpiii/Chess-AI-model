import os
# Silence TensorFlow logs before any imports
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np
import argparse
import mlflow
import mlflow.pytorch
import yaml
from src.core.model.maia_arch import MaiaNet
from src.core.model.maia_weights import load_maia_weights

def finetune(weights_path, data_path, output_path, epochs=3, batch_size=512, lr=1e-4, config_path=None):
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            epochs = config.get('finetune_epochs', epochs)
            lr = config.get('finetune_lr', lr)
            batch_size = config.get('finetune_batch_size', batch_size)
            print(f"Loaded config from {config_path}: Epochs={epochs}, LR={lr}, BatchSize={batch_size}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    mlflow.set_experiment("maia-fine-tuning")
    
    with mlflow.start_run():
        mlflow.log_params({
            "initial_weights": weights_path,
            "data_path": data_path,
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "device": str(device)
        })
        if config_path and 'config' in locals():
            mlflow.set_tag("user", config.get("username", "unknown"))
        elif config_path and os.path.exists(config_path): # Re-load if not in locals
             with open(config_path, 'r') as f:
                c = yaml.safe_load(f)
                mlflow.set_tag("user", c.get("username", "unknown"))
        
        if device.type == "cuda":
            print(f"SUCCESS: Training on GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("WARNING: GPU NOT FOUND. Training on CPU.")
        
        model = MaiaNet().to(device)
        print(f"Loading official weights from {weights_path}...")
        load_maia_weights(model, weights_path)
        
        print(f"Loading data from {data_path}...")
        data = np.load(data_path)
        boards = torch.from_numpy(data['boards'])
        moves = torch.from_numpy(data['moves']).long()
        
        full_dataset = TensorDataset(boards, moves)
        val_size = int(0.1 * len(full_dataset))
        train_size = len(full_dataset) - val_size
        train_ds, val_ds = random_split(full_dataset, [train_size, val_size])
        
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, pin_memory=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size, pin_memory=True)
        
        optimizer = optim.Adam(model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()
        
        best_val_acc = 0.0
        
        for epoch in range(epochs):
            model.train()
            total_train_loss = 0
            train_correct = 0
            
            for i, (b, m) in enumerate(train_loader):
                b, m = b.to(device, non_blocking=True), m.to(device, non_blocking=True)
                b = b.float()
                
                optimizer.zero_grad()
                policy, _ = model(b)
                loss = criterion(policy, m)
                loss.backward()
                optimizer.step()
                
                total_train_loss += loss.item()
                train_correct += (policy.argmax(1) == m).sum().item()
                
                if i % 100 == 0:
                    print(f"Epoch {epoch+1}/{epochs} | Batch {i}/{len(train_loader)} | Loss: {loss.item():.4f}")
            
            model.eval()
            total_val_loss = 0
            val_correct = 0
            with torch.no_grad():
                for b, m in val_loader:
                    b, m = b.to(device), m.to(device)
                    policy, _ = model(b.float())
                    total_val_loss += criterion(policy, m).item()
                    val_correct += (policy.argmax(1) == m).sum().item()
            
            avg_train_loss = total_train_loss / len(train_loader)
            avg_val_loss = total_val_loss / len(val_loader)
            train_acc = train_correct / train_size
            val_acc = val_correct / val_size
            
            mlflow.log_metrics({
                "train_loss": avg_train_loss,
                "val_loss": avg_val_loss,
                "train_acc": train_acc,
                "val_acc": val_acc
            }, step=epoch)
            
            print(f"--- Epoch {epoch+1} Results: Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.4f} ---")
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                torch.save(model.state_dict(), output_path)
                mlflow.log_artifact(output_path)
        
        mlflow.log_metric("best_val_acc", best_val_acc)
        print(f"Successfully finished finetuning. Best Val Accuracy: {best_val_acc:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=512)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--config", help="Path to config.yaml")
    args = parser.parse_args()
    
    finetune(args.weights, args.data, args.output, args.epochs, args.batch_size, args.lr, args.config)
