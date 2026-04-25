# Maia Finetuning

## What Maia is

[Maia](https://maiachess.com/) is a chess engine built by researchers at Cornell and University of Toronto. Unlike Stockfish, which is designed to play the best move, Maia is designed to predict the move a human player would make.

It's built on the Lc0 (Leela Chess Zero) architecture — a convolutional neural network that takes a 112-plane board representation as input and outputs a policy over 1858 possible moves. The key contribution is that it was trained on human games filtered by ELO bucket, so `maia_1100` predicts what a 1100-rated human would do, `maia_1200` predicts a 1200-rated human, and so on.

The original Maia models are available as Lc0 `.pb.gz` files. This project loads those weights into a PyTorch reimplementation (`MaiaNet`), then finetunes on your specific games.

## Architecture: MaiaNet

```
Input: (batch, 112, 8, 8)
  → Conv2d(112, 64, 3, padding=1) + BN + ReLU          [input conv]
  → SEResBlock × 6                                       [body]
  → Policy head → matmul(policy_map) → (batch, 1858)    [policy]
  → Value head → (batch, 3)                              [value: win/draw/loss]
```

The key difference from ChessNet is the **Squeeze-and-Excitation block** in each residual block. SE blocks let the network recalibrate channel weights globally — useful for chess because the importance of different piece types changes dramatically by position.

The policy head outputs 80×8×8 = 5120 values, then multiplies by `policy_map` (a fixed 5120×1858 matrix from Lc0) to produce the final 1858 move logits. This mapping is baked into the original Maia architecture and must be preserved exactly.

## Loading the pretrained weights

Maia's pretrained weights are stored as Lc0 protobuf files (`.pb.gz`). Loading them into PyTorch requires:

1. Parsing the protobuf format using TensorFlow's protobuf library
2. Mapping the Lc0 weight names to PyTorch parameter names
3. Handling the SE block's specific weight layout

This is done in `src/core/model/maia_weights.py`. It's why TensorFlow is in the dependencies — not for training, just for reading the `.pb.gz` format.

## The training data format

The Maia finetuning data is prepared by `src/maia/prepare_data_custom.py`. For each position where you made a move:

1. Encode the board as a 112-plane tensor (`board_to_maia_tensor`)
2. Encode your move as an index into the 1858-element policy vector (`move_to_maia_index`)
3. Save both as numpy arrays in a `.npz` file

The critical detail: positions are always encoded **from the perspective of the side to move**. When it's black's turn, the board is mirrored vertically (ranks flipped, files stay the same) and piece colors are swapped. This is `chess.Board.mirror()` in python-chess. Black's move is also mirrored before being looked up in the policy index. This is the same convention Lc0 uses.

## Finetuning loop

- **Loss**: Cross-entropy on the move index (same as behavioral)
- **Optimizer**: Adam, `lr=0.00001` (very low — we're finetuning, not training from scratch)
- **Epochs**: 20
- **Batch size**: 512
- **Validation split**: 10%
- **Checkpoint**: saves best val accuracy to `models/maia_{ELO}_finetuned.pt`

The low learning rate matters. Starting from a strong pretrained checkpoint and using a high LR will destroy the learned representations and produce a worse model than the base Maia. With `lr=0.00001`, finetuning nudges the weights toward your games without forgetting what the base model learned.

## Evaluating finetuning quality

`make maia-evaluate` runs `src/evaluation/compare_maia.py` which measures **move match rate**: given a position from your games, what percentage of the time does each model predict the move you actually played?

A higher move match rate doesn't necessarily mean the model plays better chess — it means it plays more like you. That's the goal.

## Why not just use the base Maia?

You could. The base `maia_1100` already plays in a human-like way at 1100 ELO. Finetuning adds your specific tendencies — your preferred openings, your tendency to trade pieces early or late, your endgame patterns. The difference is noticeable if you have enough games (500+). With fewer games, the improvement is marginal.

## The 1858 move policy

Lc0 uses a specific encoding of chess moves called the policy index. It encodes moves as (from_square, to_square, promotion_piece) with a few special cases. There are exactly 1858 valid entries. The list is provided by the `maia-chess` repository (`maia_chess_backend.maia.policy_index`).

When looking up a move in the policy index for black, the squares must be mirrored to match the from-black's-perspective board encoding. A move from e7 to e5 for black becomes e2 to e4 in the policy index (rank flip: r → 9-r).
