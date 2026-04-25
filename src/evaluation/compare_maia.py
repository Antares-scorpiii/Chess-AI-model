import torch
import chess
import chess.pgn
import argparse
import os
import pandas as pd
from tqdm import tqdm
from src.core.model.maia_arch import MaiaNet
from src.core.model.maia_weights import load_maia_weights
from src.core.data.features import board_to_maia_tensor, move_to_maia_index

def evaluate_model(model, device, pgn_path, samples=100):
    model.eval()
    correct = 0
    total = 0
    
    with open(pgn_path) as f:
        for _ in range(samples):
            game = chess.pgn.read_game(f)
            if game is None: break
            
            board = game.board()
            for move in game.mainline_moves():
                tensor = torch.from_numpy(board_to_maia_tensor(board)).unsqueeze(0).to(device)
                
                with torch.no_grad():
                    logits, _ = model(tensor)
                    pred_idx = torch.argmax(logits, dim=1).item()
                
                actual_idx = move_to_maia_index(move, board)
                
                if actual_idx is not None:
                    if pred_idx == actual_idx:
                        correct += 1
                    total += 1
                
                board.push(move)
                
    return correct / total if total > 0 else 0

def compare_maia_models(original_weights_path, finetuned_path, pgn_path, samples=100):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    results = []
    
    print(f"Loading Original Weights from {original_weights_path}...")
    model = MaiaNet().to(device)
    load_maia_weights(model, original_weights_path)
    acc = evaluate_model(model, device, pgn_path, samples)
    results.append({"Model": "Original", "Accuracy": acc})
    print(f"Original Accuracy: {acc*100:.2f}%")
    
    print(f"Loading Fine-tuned Weights from {finetuned_path}...")
    # Load state dict for fine-tuned .pt file
    model = MaiaNet().to(device)
    model.load_state_dict(torch.load(finetuned_path, weights_only=True))
    acc = evaluate_model(model, device, pgn_path, samples)
    results.append({"Model": "Fine-tuned", "Accuracy": acc})
    print(f"Fine-tuned Accuracy: {acc*100:.2f}%")
    
    df = pd.DataFrame(results)
    print("\nComparison results:")
    print(df)
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/maia_comparison.csv", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True)
    parser.add_argument("--finetuned", required=True)
    parser.add_argument("--pgn", required=True)
    parser.add_argument("--samples", type=int, default=50)
    args = parser.parse_args()
    
    # Determine the correct paths
    # The finetune target saves to models/maia_1100_finetuned.pt by default in Makefile
    compare_maia_models(args.original, args.finetuned, args.pgn, args.samples)
