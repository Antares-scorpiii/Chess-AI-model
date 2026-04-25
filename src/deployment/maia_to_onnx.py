import torch
import sys
import os
import argparse
import json

# Add Maia to path
maia_path = os.path.join(os.getcwd(), "external/maia-chess/move_prediction")
if maia_path not in sys.path:
    sys.path.append(maia_path)

from src.core.model.maia_arch import MaiaNet

def convert_to_onnx(weights_path, output_path):
    """Convert Maia PyTorch model to ONNX (keeps 1858 outputs)"""
    
    # Load model
    print(f"Loading weights from {weights_path}...")
    model = MaiaNet()
    
    # Load weights
    checkpoint = torch.load(weights_path, map_location='cpu', weights_only=False)
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        model.load_state_dict(checkpoint)
    
    model.eval()
    
    # Create dummy input (112 planes, 8x8 board)
    dummy_input = torch.randn(1, 112, 8, 8)
    
    # Export to ONNX
    print(f"Exporting to {output_path}...")
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        input_names=["board"],
        output_names=["policy_logits", "value"],
        dynamic_axes={"board": {0: "batch"}},
        opset_version=11,
        dynamo=False
    )
    
    print(f"✓ ONNX model exported: {output_path}")
    
    # CRITICAL: Export policy index as JSON for the web UI
    try:
        from maia_chess_backend.maia.policy_index import policy_index
        
        # Policy index is a LIST where index = policy index, value = UCI move
        # We need to create a dict: UCI move -> policy index for fast lookup
        policy_dict = {}
        for idx, uci_move in enumerate(policy_index):
            policy_dict[uci_move] = idx
        
        # Save as JSON
        output_dir = os.path.dirname(output_path)
        policy_json_path = os.path.join(output_dir, "maia_policy_index.json")
        
        with open(policy_json_path, "w") as f:
            json.dump(policy_dict, f)
        
        print(f"✓ Policy index exported: {policy_json_path}")
        print(f"  Total moves: {len(policy_dict)}")
        
    except Exception as e:
        print(f"⚠ Warning: Could not export policy index: {e}")
        print("  The model will work but move decoding might be suboptimal")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True, help="Path to PyTorch weights (.pt or .txt)")
    parser.add_argument("--output", default="static/maia_model/maia_model.onnx")
    args = parser.parse_args()
    
    convert_to_onnx(args.weights, args.output)