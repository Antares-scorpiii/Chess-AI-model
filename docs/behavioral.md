# Behavioral Cloning Model

## What it does

Behavioral cloning frames move prediction as a classification problem. For every position you faced in your Lichess games, the model is given the board state and trained to predict which move you played. At inference time, it scores all legal moves and picks the one with the highest logit.

This is the simplest possible approach to building a personal chess AI. It doesn't understand chess in any deep sense — it's learning a statistical map from positions to your moves.

## Architecture: ChessNet

```
Input: (batch, 19, 8, 8)
  → Conv2d(19, channels, 3, padding=1) + BN + ReLU       [input conv]
  → ResBlock × num_res_blocks                              [body]
  → Flatten → Linear(channels*64, 512) → ReLU → Dropout   [policy head]
  → Linear(512, 4096)                                      [output]
```

The output is 4096 logits — one for every possible (from_square, to_square) pair (64 × 64). Illegal moves just get low scores since they're never in the training data. At inference, we take only the highest-scoring legal move.

### Why 4096 outputs?

The simplest encoding: a move is a (from, to) pair. 64 squares × 64 squares = 4096. This over-counts — most pairs are illegal — but it avoids having to maintain a separate move indexing scheme. The behavioral model doesn't deal with promotions separately; queen promotion is assumed by default.

### Residual blocks

Each ResBlock is:
```
x → Conv → BN → ReLU → Conv → BN → (+residual) → ReLU
```

No squeeze-and-excitation (unlike Maia). Simpler, faster to train, good enough for behavioral cloning.

### Config options

| Parameter | Default | What it does |
|-----------|---------|--------------|
| `channels` | 64 | Width of all conv layers |
| `num_res_blocks` | 4 | Depth of the residual body |
| `dropout` | 0.15 | Dropout in policy head |
| `use_value_head` | false | Adds a value prediction head (unused in inference) |
| `lr` | 0.0001 | Initial learning rate |
| `lr_scheduler` | cosine | `cosine` or `step` |
| `epochs` | 30 | Max training epochs |

## Training loop

- **Loss**: Cross-entropy on the move index
- **Optimizer**: Adam with `weight_decay=0.0005`
- **LR schedule**: Cosine annealing over all epochs
- **Gradient clipping**: norm 1.0
- **Early stopping**: patience 5 epochs on val accuracy
- **Validation split**: 10% held out randomly

The training loop logs `train_loss`, `val_loss`, `train_acc`, `val_acc`, and `top5_val_acc` to MLflow at every epoch.

`top5_val_acc` is usually more meaningful than top-1 — if your actual move is in the top 5 predictions, the model understands the position even if it doesn't rank your exact choice first.

## What the model learns (and doesn't)

It learns opening tendencies — if you always play the Sicilian, it will too. It learns your tactical habits at a surface level. It doesn't learn anything about the clock, game phase transitions, or opponent-specific adjustments.

The biggest limitation is data sparsity: most positions are unique. The model is essentially interpolating from the nearest positions it's seen. This works fine in the opening but degrades in complex middlegames and endgames where your game history has thin coverage.

## Alternative approaches considered

**Monte Carlo Tree Search on top of the policy network**: Would produce stronger play but defeats the point — we want it to play like you, not play well.

**Recurrent models over move sequences**: Could capture temporal patterns in your games (e.g., you tend to castle early) but significantly more complex to train and the gains over a position-only model are marginal for this use case.

**Separate value head**: The architecture supports it (`use_value_head: true`) but it's off by default. Training a value head from behavioral cloning data is noisy — the game result isn't a good signal for position quality from an intermediate position.
