USERNAME := $(shell grep "username:" config.yaml | cut -d '"' -f 2)
ELO      := $(shell grep "ELO:" config.yaml | cut -d ' ' -f 2 || echo 1100)

# ── Install ────────────────────────────────────────────────────────────────────
install:
	uv sync

# ── Behavioral pipeline ────────────────────────────────────────────────────────
behav-download:
	uv run python src/core/data/download.py --username $(USERNAME) --output data/games.pgn

behav-dataset:
	uv run python -m src.core.data.build_dataset --pgn data/games.pgn --username $(USERNAME) --output data/dataset.h5

behav-train:
	uv run python -m src.behavioral.train --config config.yaml

behav-evaluate:
	uv run python -m src.evaluation.evaluate --config config.yaml --samples 200

behav-export:
	uv run python -m src.deployment.export --config config.yaml

behav-quantize:
	uv run python -m src.deployment.quantize --config config.yaml --input static/behavioral_model/model.onnx --output static/behavioral_model/model_quantized.onnx --op-types MatMul,Gemm

behav-all: behav-download behav-dataset behav-train behav-evaluate behav-export behav-quantize

# ── Maia pipeline ──────────────────────────────────────────────────────────────
maia-download:
	uv run python src/maia/download_weights.py

maia-dataset:
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.maia.prepare_data_custom --input data/games.pgn --output data/maia_chunks --config config.yaml

maia-finetune:
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.maia.finetune_pytorch --weights external/maia-chess/move_prediction/model_files/$(ELO)/final_$(ELO)-40.pb.gz --data data/maia_chunks/training_data.npz --output models/maia_$(ELO)_finetuned.pt --config config.yaml

maia-evaluate:
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.evaluation.compare_maia --original external/maia-chess/move_prediction/model_files/$(ELO)/final_$(ELO)-40.pb.gz --finetuned models/maia_$(ELO)_finetuned.pt --pgn data/games.pgn --samples 100

maia-export:
	mkdir -p static/maia_model
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.deployment.maia_to_onnx --weights models/maia_$(ELO)_finetuned.pt --output static/maia_model/maia_model.onnx

maia-quantize:
	uv run python -m src.deployment.quantize --config config.yaml --input static/maia_model/maia_model.onnx --output static/maia_model/maia_model_quantized.onnx --op-types MatMul,Gemm

maia-all: maia-download maia-dataset maia-finetune maia-evaluate maia-export maia-quantize

# ── Serve ──────────────────────────────────────────────────────────────────────
serve:
	uv run python -m http.server 8080 --directory static
