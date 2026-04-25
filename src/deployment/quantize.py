from onnxruntime.quantization import quantize_dynamic, QuantType
from onnxruntime.quantization.shape_inference import quant_pre_process
import yaml
import argparse
import os

def quantize_model(config: dict, op_types=None):
    input_path = config["onnx_output_path"]
    output_path = config["quantized_output_path"]
    prep_path = input_path.replace(".onnx", "_prep.onnx")

    if not os.path.exists(input_path):
        print(f"ONNX model not found at {input_path}. Please run 'make export' first.")
        return

    print("Running ONNX pre-processing...")
    quant_pre_process(input_path, prep_path, skip_symbolic_shape=True)

    print("Running dynamic quantization...")
    quantize_dynamic(
        model_input=prep_path,
        model_output=output_path,
        weight_type=QuantType.QInt8,
        op_types_to_quantize=op_types,
        extra_options={'EnableSubgraph': True}
    )
    
    original_size = os.path.getsize(input_path) / (1024 * 1024)
    quantized_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Original: {original_size:.1f}MB → Quantized: {quantized_size:.1f}MB")
    print(f"Size reduction: {(1 - quantized_size/original_size)*100:.0f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", help="Optional override for input ONNX path")
    parser.add_argument("--output", help="Optional override for output quantized path")
    parser.add_argument("--op-types", help="Comma-separated op types to quantize (default: all)")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    if args.input:
        config["onnx_output_path"] = args.input
    if args.output:
        config["quantized_output_path"] = args.output

    op_types = [op.strip() for op in args.op_types.split(",")] if args.op_types else None
    quantize_model(config, op_types)
