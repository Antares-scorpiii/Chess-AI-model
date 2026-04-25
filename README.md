# Chess AI

Two chess models served in a Lichess-style browser interface, switchable at runtime without reloading the page.

- **Behavioral cloning model** — trained on your own Lichess games to mimic your style
- **Maia finetuned model** — Maia 1300 (Lc0-based) finetuned on your games to play like you at that ELO

Both models run fully client-side via ONNX Runtime Web (no server, no GPU).

---

## Architecture

```
src/
  behavioral/       # Behavioral cloning training
  maia/             # Maia finetuning pipeline
  core/
    data/           # PGN download, dataset building, feature encoding
    model/          # MaiaNet architecture, weights loader
  deployment/       # ONNX export + quantization
  evaluation/       # Model comparison scripts
static/             # Frontend (vanilla JS + Chessground)
  behavioral_model/ # Quantized behavioral ONNX
  maia_model/       # Quantized Maia ONNX + policy index
```

---

## Quickstart

```bash
uv sync
```

**Behavioral pipeline** (train on your Lichess games):
```bash
make behav-download   # fetch PGN from Lichess
make behav-dataset    # build HDF5 dataset
make behav-train      # train behavioral cloning model
make behav-evaluate   # evaluate on held-out games
make behav-export     # export to ONNX
make behav-quantize   # INT8 quantize
# or: make behav-all
```

**Maia finetuning pipeline**:
```bash
make maia-download    # download Maia 1100 pretrained weights
make maia-dataset     # prepare Lc0-format training data
make maia-finetune    # finetune on your games
make maia-evaluate    # compare finetuned vs original Maia
make maia-export      # export to ONNX
make maia-quantize    # INT8 quantize
# or: make maia-all
```

**Serve**:
```bash
make serve            # http://localhost:8080
```

---

## Config

Copy and edit `config.yaml`:
```yaml
username: "your_lichess_username"
ELO: 1100
```

---

## How it works

**Behavioral model** — 19-plane board encoding (pieces, castling, side-to-move, 50-move rule). Outputs 4096 logits (from × to), picks the highest-scoring legal move.

**Maia model** — 112-plane Lc0 encoding (8 history timesteps × 13 planes + 8 metadata planes). Board is mirrored vertically for black's turn. Outputs 1858 logits mapped via the Lc0 policy index.

Both models are INT8 quantized (~75% size reduction) for fast browser inference.

---

## Dependencies

- [python-chess](https://python-chess.readthedocs.io/)
- [PyTorch](https://pytorch.org/)
- [ONNX Runtime](https://onnxruntime.ai/)
- [MLflow](https://mlflow.org/) — training experiment tracking
- [Maia Chess](https://github.com/CSSLab/maia-chess) — base model + policy index
- [Chessground](https://github.com/lichess-org/chessground) — board UI
- [chess.js](https://github.com/jhlywa/chess.js) — move legality

LinkedIn post:

I built a chess AI that plays like me.

Two models, both trained on my own Lichess game history:

→ A behavioral cloning model that learns my move patterns directly from PGN data
→ A finetuned Maia model (ELO 1100) that adapts the Lc0-based Maia architecture to my specific playing style

Both run entirely in the browser — no backend, no GPU. The models are INT8 quantized and served via ONNX Runtime Web. You can toggle between them mid-game without reloading.

The full pipeline: download games from Lichess → build dataset → train → evaluate → export to ONNX → quantize → serve.

Built with PyTorch, ONNX Runtime, Chessground, and chess.js.

[link]

MLflow charts — your training metrics are stored in MLflow but only as raw metric logs (no images). To get charts:


uv run mlflow ui
Opens at http://localhost:5000. Go to your run → Charts tab. You can screenshot from there, or click the download icon on any chart to save it as PNG.

Vercel deployment:

The static/ folder is a pure static site. Deploy it directly:


npm i -g vercel
cd static
vercel
Vercel will detect it as a static site. Done — no config needed. The ONNX models in static/maia_model/ and static/behavioral_model/ will be served as static assets.

One caveat: maia_model.onnx has a .data sidecar file (external weights). Make sure both maia_model.onnx and maia_model.onnx.data are not in your .gitignore before deploying — only the full (non-quantized) versions are ignored. The quantized files (*_quantized.onnx) are kept and will deploy fine.