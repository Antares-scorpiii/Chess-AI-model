# Chess AI

I wanted to build a chess AI that plays like me — not like Stockfish, not like a generic bot. Something that makes the same kinds of moves I would make, including the mistakes.

This project does that two ways. First, a behavioral cloning model trained directly on my Lichess game history. Second, a finetuned version of [Maia](https://maiachess.com/) — a human-like chess model built on the Lc0 architecture — adapted specifically to my playing style at my ELO.

Both models run entirely in the browser via ONNX Runtime Web. No backend server, no GPU required. You can toggle between them mid-game.

---

## What's in here

- Full training pipeline: download games → build dataset → train → evaluate → export → quantize
- Two model architectures: a simple residual net for behavioral cloning, and MaiaNet (SE-ResNet) for Maia finetuning
- A Lichess-style frontend (Chessground + chess.js) that runs inference client-side
- INT8 quantization that skips Conv layers (browser ONNX Runtime doesn't support ConvInteger)
- MLflow experiment tracking for both training runs

---

## Quickstart

You need Python 3.13, [uv](https://docs.astral.sh/uv/), and a Lichess account.

```bash
git clone <this-repo>
cd chess-ai
uv sync
```

Copy `config.yaml` and fill in your details:

```yaml
username: "your_lichess_username"
ELO: 1100   # or 1200, 1300 — picks the Maia base checkpoint
```

**Behavioral model** (trains on your move history):
```bash
make behav-download    # pulls your PGN from Lichess API
make behav-dataset     # builds HDF5 dataset with 19-plane board encoding
make behav-train       # trains ChessNet with cosine LR schedule
make behav-evaluate    # evaluates move prediction accuracy
make behav-export      # exports to ONNX
make behav-quantize    # INT8 quantize (MatMul/Gemm only — browser safe)

# or just: make behav-all
```

**Maia finetuning** (adapts Maia to your style):
```bash
make maia-download     # downloads Maia pretrained weights (.pb.gz)
make maia-dataset      # converts PGN to Lc0-format numpy arrays
make maia-finetune     # finetuning run on your games
make maia-evaluate     # compare finetuned vs original Maia move match rate
make maia-export       # export to ONNX (opset 17)
make maia-quantize     # INT8 quantize (MatMul/Gemm only)

# or just: make maia-all
```

**Serve:**
```bash
make serve    # http://localhost:8080
```

---

## Why two models

The behavioral model is simpler and faster to train. It learns a direct mapping from board position to move using cross-entropy on your game history. It picks up your patterns but doesn't understand chess style at a deeper level.

Maia was specifically designed to predict human moves at specific ELO levels. Finetuning it on your games is a much stronger starting point — the base model already understands human-like play, and finetuning shifts it toward your personal tendencies.

---

## Full documentation

```bash
uv run mkdocs serve
```

Covers the board encoding format, model architectures, quantization decisions, frontend design, and everything that broke along the way.
