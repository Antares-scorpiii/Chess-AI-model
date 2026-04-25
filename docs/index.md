# Chess AI

This project trains two different chess models on your personal Lichess game history and serves them in a browser-based interface. The goal isn't to build the strongest engine — it's to build one that plays like *you*.

## The idea

Most chess engines optimize for best play. Maia flipped this: instead of asking "what's the best move?", it asks "what move would a human at this ELO play?" This project takes that further — instead of a generic 1100-rated human, what move would *you* play?

## Two approaches

**Behavioral cloning** — treat your game history as a dataset. For every position you faced, record which move you played. Train a neural network to predict that move given the board. Simple, fast, works reasonably well.

**Maia finetuning** — start from a pretrained Maia checkpoint (which already understands human-like chess at a given ELO) and finetune it on your specific games. More expensive to set up but produces a stronger model because the base already has deep knowledge of human patterns.

## How it runs

Both models are exported to ONNX and INT8 quantized, then loaded directly in the browser using ONNX Runtime Web. There is no server doing inference — everything runs in the user's browser tab via WebAssembly.

## Navigation

- **[Getting Started](setup.md)** — clone, configure, run
- **[Behavioral Cloning](behavioral.md)** — the architecture, training loop, and what the model actually learns
- **[Maia Finetuning](maia.md)** — what Maia is, how finetuning works, what the data looks like
- **[Board Encoding](encoding.md)** — the 19-plane and 112-plane formats in detail
- **[ONNX Export & Quantization](deployment.md)** — getting PyTorch models into the browser
- **[Browser Inference](browser.md)** — ONNX Runtime Web, the ConvInteger problem, and how we fixed it
- **[Frontend](frontend.md)** — Chessground, chess.js, the model toggle
- **[References](references.md)** — papers, tools, and resources
