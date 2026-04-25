import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
import mlflow
import yaml
import argparse
import os
from src.core.model.chess_net import ChessNet
from src.core.model.dataset import ChessDataset

def train(config: dict):
    mlflow.set_experiment("chess-behavioral-cloning")
    
    with mlflow.start_run():
        mlflow.log_params(config)
        mlflow.set_tag("user", config.get("username", "unknown"))
        
        if not os.path.exists(config["dataset_path"]):
            print(f"Dataset not found at {config['dataset_path']}. Please run 'make dataset' first.")
            return

        dataset = ChessDataset(config["dataset_path"])
        val_size = int(0.1 * len(dataset))
        train_size = len(dataset) - val_size
        train_ds, val_ds = random_split(dataset, [train_size, val_size])
        
        train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=config["batch_size"], num_workers=0)
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")
        
        model = ChessNet(
            channels=config["channels"],
            num_res_blocks=config["num_res_blocks"],
            use_value_head=config.get("use_value_head", False),
            dropout=config.get("dropout", 0.3)
        ).to(device)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"], weight_decay=config.get("weight_decay", 1e-4))
        
        if config.get("lr_scheduler") == "cosine":
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config["epochs"])
        else:
            scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
            
        criterion = nn.CrossEntropyLoss()
        
        best_val_acc = 0.0
        epochs_no_improve = 0
        patience = config.get("early_stopping_patience", 5)
        os.makedirs(os.path.dirname(config["checkpoint_path"]), exist_ok=True)
        
        for epoch in range(config["epochs"]):
            model.train()
            train_loss, train_correct = 0.0, 0
            
            for boards, moves, results in train_loader:
                boards, moves = boards.to(device), moves.to(device)
                
                optimizer.zero_grad()
                logits = model(boards)
                loss = criterion(logits, moves)
                loss.backward()
                
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                
                train_loss += loss.item()
                train_correct += (logits.argmax(1) == moves).sum().item()
            
            model.eval()
            val_loss, val_correct, top5_correct = 0.0, 0, 0
            
            with torch.no_grad():
                for boards, moves, results in val_loader:
                    boards, moves = boards.to(device), moves.to(device)
                    logits = model(boards)
                    val_loss += criterion(logits, moves).item()
                    val_correct += (logits.argmax(1) == moves).sum().item()
                    top5_correct += (logits.topk(5, dim=1).indices == moves.unsqueeze(1)).any(dim=1).sum().item()
            
            train_acc = train_correct / train_size
            val_acc = val_correct / val_size
            top5_acc = top5_correct / val_size
            
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            scheduler.step()
            
            mlflow.log_metrics({
                "train_loss": avg_train_loss,
                "val_loss": avg_val_loss,
                "train_acc": train_acc,
                "val_acc": val_acc,
                "top5_val_acc": top5_acc,
            }, step=epoch)
            
            print(f"Epoch {epoch+1:3d} | Train Acc: {train_acc:.3f} | Val Acc: {val_acc:.3f} | Top-5: {top5_acc:.3f}")
            
            if val_acc > best_val_acc + 0.001:
                best_val_acc = val_acc
                epochs_no_improve = 0
                torch.save(model.state_dict(), config["checkpoint_path"])
                mlflow.log_artifact(config["checkpoint_path"])
            else:
                epochs_no_improve += 1
                
            if epochs_no_improve >= patience:
                print(f"\nEarly stopping triggered! Validation accuracy hasn't improved significantly in {patience} epochs.")
                break
        
        print(f"\nBest Val Accuracy: {best_val_acc:.3f}")
        mlflow.log_metric("best_val_acc", best_val_acc)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
    
    train(config)
