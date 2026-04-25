# Automatically extract username from config.yaml
USERNAME := $(shell grep "username:" config.yaml | cut -d '"' -f 2)
ELO := $(shell grep "ELO:" config.yaml | cut -d ' ' -f 2 || echo 1100)

install:
	uv sync

download:
	uv run python src/core/data/download.py --username $(USERNAME) --output data/games.pgn

dataset:
	uv run python -m src.core.data.build_dataset --pgn data/games.pgn --username $(USERNAME) --output data/dataset.h5

train:
	uv run python -m src.behavioral.train --config config.yaml

export:
	uv run python -m src.deployment.export --config config.yaml

quantize:
	uv run python -m src.deployment.quantize --config config.yaml

all: download dataset train export quantize

serve:
	uv run python -m http.server 8080 --directory static

evaluate:
	uv run python -m src.evaluation.evaluate --config config.yaml --samples 200
####

download-maia:
	uv run python src/maia/download_weights.py

compare:
	uv run python -m src.evaluation.compare_checkpoints --config config.yaml

ELO ?= 1200

maia-prep-data:
	@echo "Preparing Maia training data for $(USERNAME)..."
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.maia.prepare_data_custom --input data/games.pgn --output data/maia_chunks --config config.yaml

maia-finetune:
	@echo "Fine-tuning Maia with PyTorch..."
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.maia.finetune_pytorch --weights external/maia-chess/move_prediction/model_files/$(ELO)/final_$(ELO)-40.pb.gz --data data/maia_chunks/training_data.npz --output models/maia_$(ELO)_finetuned.pt --config config.yaml

maia-evaluate:
	@echo "Evaluating Maia models..."
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.evaluation.compare_maia --original external/maia-chess/move_prediction/model_files/$(ELO)/final_$(ELO)-40.pb.gz --finetuned models/maia_$(ELO)_finetuned.pt --pgn data/games.pgn --samples 100
maia-export:
	mkdir -p static/maia_model
	PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python uv run python -m src.deployment.maia_to_onnx --weights models/maia_model/maia_finetuned.txt --output static/maia_model/maia_model.onnx
maia-quantize:
	uv run python -m src.deployment.quantize --config config.yaml --input static/maia_model/maia_model.onnx --output static/maia_model/maia_model_quantized.onnx

# Model switching targets
serve-behavior:
	@echo "Setting up behavioral model..."
	uv run python scripts/set_model.py behavior
	@echo "Starting server on http://localhost:8080"
	uv run python -m http.server 8080 --directory static
 
serve-maia:
	@echo "Setting up Maia model..."
	uv run python scripts/set_model.py maia
	@echo "Starting server on http://localhost:8080"
	uv run python -m http.server 8080 --directory static
 
# Keep old serve for backwards compatibility (defaults to behavior)
serve:
	@echo "Using default behavioral model. Use 'make serve-behavior' or 'make serve-maia' to choose."
	uv run python scripts/set_model.py behavior
	uv run python -m http.server 8080 --directory static