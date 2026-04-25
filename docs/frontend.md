# Frontend

## Stack

- **[Chessground](https://github.com/lichess-org/chessground)** — Lichess's board rendering library. Handles piece rendering, drag-and-drop, legal move highlighting, animations
- **[chess.js](https://github.com/jhlywa/chess.js)** — move generation, legality checking, game state (checkmate, draw, etc.)
- **[ONNX Runtime Web](https://onnxruntime.ai/docs/tutorials/web/)** — runs the ONNX models in WebAssembly
- Vanilla JS, no framework

## File structure

```
static/
  index.html               # layout and script loading
  js/
    config.js              # localStorage settings persistence
    ai.js                  # ONNX inference engine
    game.js                # chess logic, clocks, sounds
    board.js               # Chessground wrapper
    ui.js                  # wires everything together
  css/
    custom.css             # full CSS (dark/light mode, 3-column layout)
  behavioral_model/
    model.onnx
    model_quantized.onnx
  maia_model/
    maia_model_quantized.onnx
    maia_policy_index.json
  model_config.json        # which model loads on startup
  model_config_behavior.json
  model_config_maia.json
```

## Model config

Each `model_config_*.json` tells the frontend where to find the models and which encoding to use:

```json
{
  "model_type": "maia",
  "model_path": "maia_model/maia_model.onnx",
  "quantized_path": "maia_model/maia_model_quantized.onnx",
  "encoding": "maia_policy_1858"
}
```

`model_config.json` is what the frontend reads on load. Changing it changes the default model.

## The model toggle

A segmented button in the left panel lets the user switch between models mid-game:

```html
<div class="model-toggle">
    <button class="model-btn" data-config="model_config_behavior.json">Behavioral</button>
    <button class="model-btn" data-config="model_config_maia.json">Maia</button>
</div>
```

On click, `ai.switchModel(configPath)` is called. This:

1. Fetches the new model config JSON
2. Loads the Maia policy index if switching to Maia (cached after first load)
3. Creates a new ONNX session for the quantized model
4. Marks the engine as ready

The game state (board position, clocks, move history) is untouched. The switch takes 1–5 seconds depending on how fast the browser can load the ONNX file.

## Settings persistence

`config.js` reads/writes to `localStorage`. Settings saved:

- `showLegalMoves`
- `playSounds`
- `autoQueen`
- `darkMode`
- `playerSide` (white/black)
- `timeControl` (seconds)

## Clocks

The clock runs a 100ms interval via `setInterval`. It decrements the active player's time. Visual states:

- Running clock: green background
- Low time (< 10 seconds): red background with pulse animation
- Timeout triggers `onGameOver`

## Game history

Completed games are tracked in-session (not persisted). The left panel shows a tally (Wins/Losses/Draws) and a list of completed games with a PGN download button for each.

## Dark/light mode

Implemented via CSS custom properties. The root defines dark mode colors, `body.theme-light` overrides them. The board colors are also overridden via `.cg-wrap .cg-square.light` and `.cg-wrap .cg-square.dark`.

## Deployment

The `static/` directory is a completely self-contained static site. To deploy to Vercel:

```bash
cd static
vercel
```

The `.vercelignore` file excludes:
- `maia_model/maia_model.onnx` (40MB full model — not needed if quantized works)
- `maia_model/maia_model.onnx.data` (external weights sidecar for the full model)
- `*_prep.onnx` (quantization intermediates)

Total deployed size: ~35MB.
