import torch
import torch.onnx
import yaml
import argparse
from src.core.model.chess_net import ChessNet

def export_to_onnx(config: dict):
    model = ChessNet(
        channels=config["channels"],
        num_res_blocks=config["num_res_blocks"]
    )
    model.load_state_dict(torch.load(config["checkpoint_path"], map_location="cpu"))
    model.eval()
    
    # 19 channels dummy input
    dummy_input = torch.zeros(1, 19, 8, 8, dtype=torch.float32)
    
    torch.onnx.export(
        model,
        dummy_input,
        config["onnx_output_path"],
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["board"],
        output_names=["policy_logits"],
        dynamo=False 
    )
    
    print(f"Exported to {config['onnx_output_path']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
    
    export_to_onnx(config)
