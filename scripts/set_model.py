#!/usr/bin/env python3
import sys
import json
import shutil
from pathlib import Path
 
def set_model(model_type):
    """Switch between behavioral and maia models by updating config"""
    
    static_dir = Path("static")
    
    if model_type == "behavior":
        config_source = static_dir / "model_config_behavior.json"
        if not config_source.exists():
            # Create default behavioral config
            config = {
                "model_type": "behavioral",
                "model_path": "behavioral_model/model.onnx",
                "quantized_path": "behavioral_model/model_quantized.onnx",
                "encoding": "from_to_64x64"
            }
            config_source.write_text(json.dumps(config, indent=2))
    
    elif model_type == "maia":
        config_source = static_dir / "model_config_maia.json"
        if not config_source.exists():
            # Create default maia config
            config = {
                "model_type": "maia",
                "model_path": "maia_model/maia_model.onnx",
                "quantized_path": "maia_model/maia_model_quantized.onnx",
                "encoding": "maia_policy_1858"
            }
            config_source.write_text(json.dumps(config, indent=2))
    
    else:
        print(f"Unknown model type: {model_type}")
        sys.exit(1)
    
    # Copy to active config
    config_dest = static_dir / "model_config.json"
    shutil.copy(config_source, config_dest)
    
    print(f"✓ Switched to {model_type} model")
    print(f"  Config: {config_source}")
    print(f"  Active: {config_dest}")
 
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_model.py [behavior|maia]")
        sys.exit(1)
    
    set_model(sys.argv[1])