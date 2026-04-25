# Browser Inference

## How it works

The frontend loads the ONNX model directly in the browser using [ONNX Runtime Web](https://onnxruntime.ai/docs/tutorials/web/). The model runs in WebAssembly — no server, no API call, no GPU. Inference happens locally in the user's tab.

```javascript
this.session = await ort.InferenceSession.create(
    'maia_model/maia_model_quantized.onnx',
    { executionProviders: ['wasm'] }
);
```

## Model loading strategy

The engine tries the quantized model first. If it fails (unsupported op, corrupted file, etc.), it falls back to the full model:

```javascript
try {
    this.session = await ort.InferenceSession.create(config.quantized_path, ...);
} catch (e) {
    this.session = await ort.InferenceSession.create(config.model_path, ...);
}
```

## The ConvInteger problem

Early versions used ONNX Runtime Web 1.14.0 and INT8 quantization on all ops. This failed with:

```
Could not find an implementation for ConvInteger(10) node
```

`ConvInteger` is an ONNX op for integer matrix multiplication, used when Conv weights are quantized to INT8. The ONNX Runtime Web WASM backend does not support it — it exists for server-side inference only.

Two fixes were applied:

1. Upgraded ONNX Runtime Web from `1.14.0` to `1.20.0`
2. Changed quantization to only quantize MatMul/Gemm layers, not Conv layers

The second fix is the definitive one. Even with a newer ORT Web version, ConvInteger in WASM is unreliable. Skipping Conv quantization avoids the problem entirely.

## Running inference

For each AI turn, `AIEngine.predict(chess)` is called:

```javascript
const inputData = this.boardToTensor(chess);  // Float32Array
const shape = isMaia ? [1, 112, 8, 8] : [1, 19, 8, 8];
const inputTensor = new ort.Tensor('float32', inputData, shape);

const results = await this.session.run({ board: inputTensor });
const logits = results.policy_logits.data;
```

The model returns logits for all possible moves. We iterate over chess.js legal moves, look up each move's index in the logit array, and pick the highest scoring one.

## ONNX Runtime Web version

The CDN is loaded from jsDelivr:

```html
<script src="https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.0/dist/ort.min.js"></script>
```

Version 1.20.0 has full WASM SIMD support and broader operator coverage than 1.14.0. If you need to pin a specific version for reproducibility, update the version number in `static/index.html`.

## Performance

Inference runs in ~50-200ms on a modern laptop (WebAssembly, single-threaded). The board adds an artificial think time (0.1–3 seconds) on top of this to feel more human:

```javascript
const thinkTime = Math.max(100, Math.min(3000, 3000 * ratio * Math.random()));
await new Promise(r => setTimeout(r, thinkTime));
```

`ratio` is the AI's remaining clock time relative to its total time — it thinks faster when low on time.
