# ONNX Export & Quantization

## Why ONNX

The goal is browser inference. ONNX Runtime Web is the best-supported path for running PyTorch models in a browser — it compiles to WebAssembly and can run without a server.

The workflow is: PyTorch `.pt` → ONNX `.onnx` → quantized `.onnx` → browser.

## Behavioral model export

`src/deployment/export.py` — uses standard `torch.onnx.export`.

```python
torch.onnx.export(
    model, dummy_input, output_path,
    input_names=["board"],
    output_names=["policy_logits"],
    dynamic_axes={"board": {0: "batch"}},
    opset_version=17
)
```

The dummy input is `(1, 19, 8, 8)`. Dynamic axes on the batch dimension means the ONNX model accepts any batch size.

## Maia model export

`src/deployment/maia_to_onnx.py` — uses the **legacy TorchScript exporter** (`dynamo=False`).

```python
torch.onnx.export(
    model, dummy_input, output_path,
    input_names=["board"],
    output_names=["policy_logits", "value"],
    dynamic_axes={"board": {0: "batch"}},
    opset_version=17,
    dynamo=False
)
```

`dynamo=False` is important. The default in newer PyTorch versions is the dynamo-based exporter, which:
- Produces models with symbolic batch dimensions that break ONNX Runtime's shape inference
- Can't be downconverted to earlier opsets
- Fails the pre-processing step required by quantization

The legacy exporter produces a clean opset-17 model that shape inference and quantization can handle.

## Quantization

`src/deployment/quantize.py` — uses ONNX Runtime's `quantize_dynamic`.

### The ConvInteger problem

Dynamic INT8 quantization converts Conv layers to use the `ConvInteger` ONNX op. This op is not supported in ONNX Runtime Web's WebAssembly backend — it exists for CPU/server use only.

If you quantize with all ops:

```python
quantize_dynamic(model_input=..., weight_type=QuantType.QInt8)
# → produces ConvInteger nodes
# → fails in browser with: "Could not find an implementation for ConvInteger(10)"
```

### The fix: skip Conv layers

Pass `op_types_to_quantize` to restrict quantization to MatMul and Gemm (the fully-connected layers):

```python
quantize_dynamic(
    model_input=prep_path,
    model_output=output_path,
    weight_type=QuantType.QInt8,
    op_types_to_quantize=["MatMul", "Gemm"],
    extra_options={"EnableSubgraph": True}
)
```

This avoids ConvInteger entirely. The tradeoff: the Conv layers (which hold most of the model's weights) stay in FP32. Size reduction is smaller than full INT8 quantization but the model actually works in the browser.

Size results with this approach:
- Behavioral: 17.2MB → 5.2MB (70% reduction)
- Maia: 39.6MB → 11.7MB (71% reduction)

### Pre-processing step

Before quantization, ONNX Runtime's `quant_pre_process` optimizes the graph (constant folding, shape inference, etc.). For models exported with the dynamo exporter, symbolic shape inference fails. With the legacy exporter and `skip_symbolic_shape=True`, it works:

```python
quant_pre_process(input_path, prep_path, skip_symbolic_shape=True)
```

The `_prep.onnx` intermediate file is gitignored — it's just a build artifact.

## Alternative: FP16 conversion

Instead of INT8 quantization, you could convert weights to FP16 using `onnxconverter_common.convert_float_to_float16`. This would:
- Halve model size (e.g. 40MB → 20MB)
- Avoid the ConvInteger problem entirely
- Require float16 inputs in the browser (JS doesn't natively support Float16Array)

We went with INT8 + `op_types_to_quantize` instead because it keeps float32 I/O, which is directly compatible with `new Float32Array(...)` in JavaScript.

## Makefile targets

```makefile
behav-quantize:
    uv run python -m src.deployment.quantize \
        --config config.yaml \
        --input static/behavioral_model/model.onnx \
        --output static/behavioral_model/model_quantized.onnx \
        --op-types MatMul,Gemm

maia-quantize:
    uv run python -m src.deployment.quantize \
        --config config.yaml \
        --input static/maia_model/maia_model.onnx \
        --output static/maia_model/maia_model_quantized.onnx \
        --op-types MatMul,Gemm
```
