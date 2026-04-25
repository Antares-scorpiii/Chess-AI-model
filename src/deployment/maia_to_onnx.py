import torch
import onnx
import argparse
import yaml
import numpy as np
from src.core.model.maia_arch import MaiaNet

def convert_to_onnx(weights_path, output_path, channels=64, blocks=6):
    model = MaiaNet(channels=channels, num_res_blocks=blocks)
    model.eval()
    
    print(f"Loading weights from {weights_path}...")
    
    dummy_input = torch.zeros(1, 112, 8, 8, dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=18,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['policy', 'value'],
        dynamo=False
    )
    print(f"Maia model exported to ONNX: {output_path}")
 
    import json
    import sys
    import os
    
    maia_path = os.path.join(os.getcwd(), "external/maia-chess/move_prediction")
    if maia_path not in sys.path:
        sys.path.append(maia_path)
    
    from maia_chess_backend.maia.policy_index import policy_index
    
    # Save policy index as JSON for the web UI
    output_dir = os.path.dirname(args.output)
    policy_index_path = os.path.join(output_dir, "maia_policy_index.json")
    
    with open(policy_index_path, "w") as f:
        json.dump(policy_index, f)
    
    print(f"Exported policy index to {policy_index_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True)
    parser.add_argument("--output", default="static/maia_model.onnx")
    args = parser.parse_args()
    
    convert_to_onnx(args.weights, args.output)
