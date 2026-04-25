# Getting Started

## Prerequisites

- Python 3.13 (exactly — the project pins to `>=3.13, <=3.14`)
- [uv](https://docs.astral.sh/uv/) for dependency management
- A Lichess account with some game history

## Clone and install

```bash
git clone <repo-url>
cd chess-ai
uv sync
```

`uv sync` reads `pyproject.toml` and installs everything into `.venv`. This includes PyTorch, TensorFlow (needed to load Maia's protobuf weights), ONNX Runtime, MLflow, and the frontend tooling.

## Config

The project is driven by a single `config.yaml`. It is gitignored because it contains your username. Create it by copying the example:

```yaml
username: "your_lichess_username"
ELO: 1100                          # 1100, 1200, or 1300 — which Maia checkpoint to finetune from

dataset_path: "data/dataset.h5"
batch_size: 128
channels: 64
num_res_blocks: 4
dropout: 0.15
weight_decay: 0.0005
lr_scheduler: "cosine"
lr: 0.0001
epochs: 30
finetune_epochs: 20
finetune_lr: 0.00001
finetune_batch_size: 128
use_value_head: false

pgn_path: "data/games.pgn"
onnx_output_path: "static/behavioral_model/model.onnx"
quantized_output_path: "static/behavioral_model/model_quantized.onnx"
checkpoint_path: "checkpoints/best_model.pt"
```

The `ELO` field controls which Maia base checkpoint gets downloaded and used for finetuning. Available options are `1100`, `1200`, and `1300`. Pick the one closest to your actual Lichess rating.

## Running the full pipelines

### Behavioral model

```bash
make behav-all
```

This runs: download → dataset → train → evaluate → export → quantize.

Or step by step:

```bash
make behav-download    # fetches your PGN from the Lichess API
make behav-dataset     # parses PGN, encodes positions as 19-plane tensors, saves to HDF5
make behav-train       # trains ChessNet, logs metrics to MLflow
make behav-evaluate    # runs evaluation on held-out positions
make behav-export      # exports to ONNX
make behav-quantize    # quantizes to INT8 (MatMul/Gemm only)
```

### Maia model

```bash
make maia-all
```

Or step by step:

```bash
make maia-download     # downloads the Maia .pb.gz checkpoint from the CSSLab release
make maia-dataset      # converts your PGN into Lc0-format numpy arrays
make maia-finetune     # runs finetuning, logs to MLflow
make maia-evaluate     # compares finetuned vs base Maia on your games
make maia-export       # exports to ONNX using TorchScript exporter (opset 17)
make maia-quantize     # quantizes to INT8 (MatMul/Gemm only)
```

### Serve

```bash
make serve
```

Opens at `http://localhost:8080`. The page loads whichever model is in `static/model_config.json` first, then you can toggle in the UI.

## Viewing training metrics

Both training scripts log to MLflow. To view the runs:

```bash
uv run mlflow ui
```

Opens at `http://localhost:5000`. Go to the relevant experiment (`chess-behavioral-cloning` or `maia-fine-tuning`), click a run, and use the Charts tab to see loss/accuracy curves. You can download charts as PNG from there.

## External dependency: maia-chess

The Maia finetuning pipeline depends on the [maia-chess](https://github.com/CSSLab/maia-chess) repository for the policy index and Lc0 policy map. It needs to live at `external/maia-chess/`. The `make maia-download` target handles this.
