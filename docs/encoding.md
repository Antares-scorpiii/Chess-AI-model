# Board Encoding

The two models use completely different board representations. Getting this exactly right is critical — a single plane in the wrong position means the model sees a nonsense board and plays random moves.

## Behavioral model: 19 planes

`src/core/data/features.py → board_to_tensor()`

```
Planes 0-5:   White pieces  (P, N, B, R, Q, K)
Planes 6-11:  Black pieces  (p, n, b, r, q, k)
Plane 12:     White kingside castling rights  (all 1s or all 0s)
Plane 13:     White queenside castling rights
Plane 14:     Black kingside castling rights
Plane 15:     Black queenside castling rights
Plane 16:     Side to move (1.0 = white, 0.0 = black)
Plane 17:     50-move rule counter / 100
Plane 18:     Clock ratio (time remaining / total time, from training)
```

**Square indexing**: python-chess square numbering, a1=0 through h8=63. In the 8×8 grid, `tensor[plane, rank, file]` where rank 0 = first rank (white's side), rank 7 = eighth rank.

For the JavaScript frontend, chess.js `board()` returns `board[row][col]` where `row=0` is rank 8 and `row=7` is rank 1. The conversion is: `sqIdx = (7 - row) * 8 + col`.

Pieces use absolute colors (white is always planes 0-5) regardless of whose turn it is. This is simpler but means the model has to learn the asymmetry explicitly.

## Maia model: 112 planes

`src/core/data/features.py → board_to_maia_tensor()`

This is the Lc0 v20/v21 input format. 112 planes total.

### Block structure

Lc0 encodes 8 history timesteps (current + 7 previous positions). Each timestep is 13 planes:

```
Planes 0-5:   Own pieces    (P, N, B, R, Q, K from current player's view)
Planes 6-11:  Opponent pieces
Plane 12:     Repetition count
```

With 8 timesteps: `8 × 13 = 104 planes`. In this project, only the current position is filled (planes 0-12). Planes 13-103 stay zero because we don't track game history.

### Metadata planes (104-111)

```
Plane 104:   Own kingside castling rights
Plane 105:   Own queenside castling rights
Plane 106:   Opponent kingside castling rights
Plane 107:   Opponent queenside castling rights
Plane 108:   Side to move (always 1.0 — board is always from current player's view)
Plane 109:   50-move rule counter / 100
Plane 110:   (unused, stays 0)
Plane 111:   All 1.0 (constant — Lc0 convention)
```

Notably plane 12 is also all 1.0 (another Lc0 constant for current-position presence).

### The perspective flip

This is the most important thing to get right. The board is **always encoded from the perspective of the side to move**.

When it's black's turn, python-chess `board.mirror()` is called. This:
1. Flips the board vertically (rank 1 ↔ rank 8, same files)
2. Swaps piece colors (black pieces become white, white becomes black)

After this, the board looks like it's white's turn playing from the other side. Own pieces are always planes 0-5.

**The key detail**: `board.mirror()` flips ranks only, not files. A piece on a7 (rank 7, file a) becomes a piece on a2 (rank 2, file a). The file doesn't change.

In JavaScript, the translation is:

```javascript
// For white: chess.js row 0 = rank 8 = python rank 7
// sqIdx = (7 - row) * 8 + col

// For black: after rank-flip, chess.js row r maps to python rank r
// sqIdx = row * 8 + col   <-- NOT (7-col), that's a file flip, wrong
```

Getting this wrong (e.g. doing a 180° rotation instead of a rank-flip) produces a board that looks plausible but encodes a completely different position. The model will produce moves, but they'll be nonsense.

### Move encoding for black

When building the training data, moves for black must be mirrored before being looked up in the policy index. Python-chess `chess.square_mirror(sq)` flips the rank: `sq ^ 56`.

In UCI notation: rank `r` → rank `(9 - r)`. So a move from e7 to e5 becomes e2 to e4 in the policy index lookup.

## Why the formats differ

The behavioral model was designed from scratch for this project. Simple absolute encoding, no history, easy to understand.

The Maia model is constrained to use the Lc0 format because the pretrained weights were trained with that encoding. Changing the encoding would require retraining from scratch and you'd lose all the value of the pretrained checkpoint.

## Verifying correctness

If the encoding is wrong, the model loads and runs without errors — it just plays badly or randomly. The easiest way to sanity-check: in the starting position, the board should have white pieces in rows 6-7 (chess.js convention), which should map to ranks 1-2 in the tensor. Print the first few planes and verify the pieces are where you expect them.
