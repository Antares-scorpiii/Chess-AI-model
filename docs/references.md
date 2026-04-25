# References

## Papers

**Maia Chess**
McIlroy-Young, R., Sen, S., Kleinberg, J., & Anderson, A. (2020).
*Aligning Superhuman AI with Human Behavior: Chess as a Model System.*
KDD 2020. [arxiv.org/abs/2006.01855](https://arxiv.org/abs/2006.01855)

The core paper behind the Maia approach — framing move prediction as human behavior modeling rather than strength optimization. Worth reading to understand why the 112-plane Lc0 encoding is used and what "move match rate" actually measures.

**Leela Chess Zero**
The Lc0 project is the open-source reimplementation of AlphaZero. The input encoding used in this project (112 planes, policy index) comes from Lc0's v20/v21 format.
[lczero.org](https://lczero.org) — [github.com/LeelaChessZero/lc0](https://github.com/LeelaChessZero/lc0)

**AlphaZero**
Silver, D. et al. (2018). *A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play.* Science 362(6419).
The architecture that Lc0 (and therefore Maia, and therefore this project) is based on.

## Code and tools

**maia-chess** (CSSLab)
[github.com/CSSLab/maia-chess](https://github.com/CSSLab/maia-chess)
Source of the pretrained Maia checkpoints and the `policy_index` + `lc0_az_policy_map` used to decode moves.

**Chessground**
[github.com/lichess-org/chessground](https://github.com/lichess-org/chessground)
Lichess's board rendering library. Used directly in the frontend.

**chess.js**
[github.com/jhlywa/chess.js](https://github.com/jhlywa/chess.js)
Move generation, legality checking, FEN/PGN parsing. The version used (0.10.3) is loaded from CDN.

**ONNX Runtime Web**
[onnxruntime.ai/docs/tutorials/web](https://onnxruntime.ai/docs/tutorials/web/)
Runs ONNX models in the browser via WebAssembly.

**python-chess**
[python-chess.readthedocs.io](https://python-chess.readthedocs.io/)
Board representation, move generation, and PGN parsing on the Python side. The `board.mirror()` function is central to the Maia encoding.

**MLflow**
[mlflow.org](https://mlflow.org)
Experiment tracking for both training runs. Run `uv run mlflow ui` to view training curves.

## Datasets

**Lichess game database**
[database.lichess.org](https://database.lichess.org)
Public game database. The project uses the Lichess API to pull a specific user's games rather than the full database.

**Lichess API**
[lichess.org/api](https://lichess.org/api) — endpoint: `GET /api/games/user/{username}`
Used by `src/core/data/download.py` to fetch your game history as PGN.

## Understanding the Lc0 input format

The 112-plane encoding is documented across a few places:

- [Lc0 input format wiki](https://github.com/LeelaChessZero/lc0/wiki/Technical-Explanation-of-Leela-Chess-Zero) — high-level description
- [lc0/src/chess/board.cc](https://github.com/LeelaChessZero/lc0/blob/master/src/chess/board.cc) — canonical implementation
- The Maia paper's supplemental material has a clean description of exactly which planes they use

The implementation in `src/core/data/features.py → board_to_maia_tensor()` was written to match this format exactly. The JavaScript version in `static/js/ai.js → _maiaBoard()` was written to match the Python implementation exactly. If they diverge, the model plays nonsense moves without throwing any errors.
