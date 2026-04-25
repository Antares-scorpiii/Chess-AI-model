# 🎯 Lichess Clone with Custom ONNX Model — Complete Build Guide

> Build a pixel-perfect Lichess interface that plays your trained chess model. Every feature, every animation, every sound — exactly like Lichess, but with your AI.

---

## 📁 PROJECT STRUCTURE

```
chess-ui/
├── index.html           # Main page
├── css/
│   └── custom.css       # Overrides and polish
├── js/
│   ├── board.js         # Chessground wrapper
│   ├── game.js          # Game state logic
│   ├── ai.js            # ONNX model interface
│   ├── ui.js            # UI controllers
│   └── config.js        # Settings persistence
├── sounds/              # Lichess sound files
│   ├── Move.ogg
│   ├── Capture.ogg
│   ├── Check.ogg
│   ├── GenericNotify.ogg
│   └── LowTime.ogg
└── models/
    ├── model.onnx
    └── model_quantized.onnx
```

---

## 🚀 SETUP INSTRUCTIONS

### Step 1: Create Project Folder
```bash
mkdir chess-ui
cd chess-ui
mkdir css js sounds models
```

### Step 2: Download Lichess Sounds
```bash
cd sounds
curl -o Move.ogg https://lichess1.org/assets/sound/standard/Move.ogg
curl -o Capture.ogg https://lichess1.org/assets/sound/standard/Capture.ogg
curl -o Check.ogg https://lichess1.org/assets/sound/standard/Check.ogg
curl -o GenericNotify.ogg https://lichess1.org/assets/sound/standard/GenericNotify.ogg
curl -o LowTime.ogg https://lichess1.org/assets/sound/standard/LowTime.ogg
cd ..
```

### Step 3: Copy Your ONNX Models
```bash
cp /path/to/your/model.onnx models/
cp /path/to/your/model_quantized.onnx models/
```

### Step 4: Create All Files (see below)

### Step 5: Run Local Server
```bash
# Python 3
python3 -m http.server 8000

# Or Python 2
python -m SimpleHTTPServer 8000

# Or if you have Node.js
npx serve
```

Open browser to `http://localhost:8000`

---

## 📄 FILE CONTENTS

### `index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chess • Play Against AI</title>
    
    <!-- Lichess Chessground Core Styles -->
    <link rel="stylesheet" href="https://unpkg.com/@lichess/chessground/assets/chessground.base.css">
    <link rel="stylesheet" href="https://unpkg.com/@lichess/chessground/assets/chessground.brown.css">
    <link rel="stylesheet" href="https://unpkg.com/@lichess/chessground/assets/chessground.cburnett.css">
    
    <!-- Custom Overrides -->
    <link rel="stylesheet" href="css/custom.css">
</head>
<body class="brown merida coords-in">
    
    <!-- Main Layout (Lichess Structure) -->
    <div class="main-board">
        
        <!-- Top Player Info -->
        <div class="ruser">
            <div class="username">AI Agent</div>
            <div class="rclock clock-wrapper">
                <div class="clock" id="clock-black">
                    <div class="time">10:00</div>
                </div>
            </div>
        </div>
        
        <!-- Board Container -->
        <div class="cg-wrap" id="board-wrapper"></div>
        
        <!-- Bottom Player Info -->
        <div class="ruser">
            <div class="username">You</div>
            <div class="rclock clock-wrapper">
                <div class="clock running" id="clock-white">
                    <div class="time">10:00</div>
                </div>
            </div>
        </div>
        
    </div>
    
    <!-- Right Panel (Lichess rmoves + controls) -->
    <div class="right-panel">
        
        <!-- Move List -->
        <div class="rmoves">
            <div class="moves" id="move-list"></div>
        </div>
        
        <!-- Game Controls -->
        <div class="rcontrols">
            <div class="status" id="status-text">Initializing...</div>
            
            <!-- Time Control Selection -->
            <div class="time-selector">
                <button class="time-button" data-time="0">∞ Unlimited</button>
                <button class="time-button" data-time="180">3+0 Blitz</button>
                <button class="time-button" data-time="300">5+0 Blitz</button>
                <button class="time-button active" data-time="600">10+0 Rapid</button>
                <button class="time-button" data-time="900">15+10 Rapid</button>
            </div>
            
            <!-- Action Buttons -->
            <div class="action-buttons">
                <button id="btn-new-game" class="button">
                    <span>New Game</span>
                </button>
                <button id="btn-takeback" class="button">
                    <span>Takeback</span>
                </button>
                <button id="btn-flip" class="button">
                    <span>Flip Board</span>
                </button>
            </div>
            
            <!-- Settings -->
            <div class="settings">
                <div class="setting-row">
                    <label>Board Theme</label>
                    <select id="board-theme">
                        <option value="brown" selected>Brown</option>
                        <option value="blue">Blue</option>
                        <option value="green">Green</option>
                        <option value="purple">Purple</option>
                        <option value="ic">IC</option>
                    </select>
                </div>
                <div class="setting-row">
                    <label>Piece Set</label>
                    <select id="piece-set">
                        <option value="cburnett" selected>Classic</option>
                        <option value="merida">Merida</option>
                        <option value="alpha">Alpha</option>
                        <option value="california">California</option>
                        <option value="cardinal">Cardinal</option>
                        <option value="pirouetti">Pirouetti</option>
                    </select>
                </div>
                <div class="setting-row">
                    <label class="checkbox-label">
                        <input type="checkbox" id="show-legal-moves" checked>
                        <span>Show legal moves</span>
                    </label>
                </div>
                <div class="setting-row">
                    <label class="checkbox-label">
                        <input type="checkbox" id="play-sounds" checked>
                        <span>Sound</span>
                    </label>
                </div>
                <div class="setting-row">
                    <label class="checkbox-label">
                        <input type="checkbox" id="premove-enabled">
                        <span>Premove</span>
                    </label>
                </div>
                <div class="setting-row">
                    <label class="checkbox-label">
                        <input type="checkbox" id="auto-queen" checked>
                        <span>Auto-promote to Queen</span>
                    </label>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Dependencies -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.13.4/chess.min.js"></script>
    <script src="https://unpkg.com/@lichess/chessground/dist/chessground.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/ort.min.js"></script>
    
    <!-- App Logic (load order matters) -->
    <script src="js/config.js"></script>
    <script src="js/ai.js"></script>
    <script src="js/game.js"></script>
    <script src="js/board.js"></script>
    <script src="js/ui.js"></script>
    
</body>
</html>
```

---

### `css/custom.css`
```css
/* Lichess-exact layout and theming */

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Noto Sans', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, Sans-Serif;
    background: #161512;
    color: #bababa;
    display: flex;
    min-height: 100vh;
    overflow: hidden;
}

/* Board Column */
.main-board {
    flex: 0 0 auto;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 1rem;
    width: 60vmin;
    max-width: 700px;
}

.cg-wrap {
    width: 100%;
    height: auto;
    aspect-ratio: 1;
}

/* Player Info */
.ruser {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0;
    color: #bababa;
}

.username {
    font-size: 1rem;
    font-weight: 600;
}

/* Clocks (Lichess style) */
.clock-wrapper {
    display: flex;
}

.clock {
    background: #3d3d3d;
    border-radius: 3px;
    padding: 0.4rem 0.8rem;
    font-family: 'Roboto Mono', monospace;
    font-size: 1.3rem;
    font-weight: bold;
    color: #bababa;
    min-width: 5rem;
    text-align: center;
}

.clock.running {
    background: #759900;
    color: #fff;
}

.clock.low-time {
    background: #dc322f;
    animation: pulse 0.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* Right Panel */
.right-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #262421;
    border-left: 1px solid #3f3d39;
    overflow-y: auto;
}

/* Move List */
.rmoves {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    border-bottom: 1px solid #3f3d39;
}

.moves {
    font-family: 'Roboto Mono', monospace;
    font-size: 0.9rem;
    line-height: 1.8;
    color: #bababa;
}

.move-pair {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
}

.move-number {
    color: #6f6f6f;
    width: 2rem;
}

.move {
    cursor: pointer;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
}

.move:hover {
    background: #3f3d39;
}

.move.active {
    background: #759900;
    color: #fff;
}

/* Controls Section */
.rcontrols {
    padding: 1.5rem;
}

.status {
    text-align: center;
    font-size: 0.95rem;
    padding: 1rem;
    background: #161512;
    border-radius: 3px;
    margin-bottom: 1.5rem;
    color: #d0d0d0;
}

/* Time Control Selector */
.time-selector {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

.time-button {
    background: #3d3d3d;
    border: 2px solid transparent;
    color: #bababa;
    padding: 0.8rem;
    border-radius: 3px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.15s;
}

.time-button:hover {
    background: #4d4d4d;
}

.time-button.active {
    background: #759900;
    color: #fff;
    border-color: #759900;
}

/* Action Buttons */
.action-buttons {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

.button {
    background: #3d3d3d;
    border: none;
    color: #bababa;
    padding: 0.7rem 1rem;
    border-radius: 3px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    transition: background 0.15s;
}

.button:hover {
    background: #4d4d4d;
}

.button:active {
    background: #2d2d2d;
}

/* Settings */
.settings {
    border-top: 1px solid #3f3d39;
    padding-top: 1rem;
}

.setting-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.setting-row label {
    font-size: 0.9rem;
    color: #bababa;
}

select {
    background: #3d3d3d;
    border: 1px solid #4d4d4d;
    color: #bababa;
    padding: 0.4rem 0.6rem;
    border-radius: 3px;
    cursor: pointer;
    font-size: 0.85rem;
}

select:focus {
    outline: none;
    border-color: #759900;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}

input[type="checkbox"] {
    width: 1.1rem;
    height: 1.1rem;
    cursor: pointer;
}

/* Coordinate labels (Lichess style) */
body.coords-in .cg-wrap {
    position: relative;
}

/* Responsive */
@media (max-width: 900px) {
    body { flex-direction: column; }
    .main-board { width: 100vmin; max-width: none; }
    .right-panel { border-left: none; border-top: 1px solid #3f3d39; }
}
```

---

### `js/config.js`
```javascript
// Settings persistence (localStorage)

const Config = {
    load() {
        const defaults = {
            boardTheme: 'brown',
            pieceSet: 'cburnett',
            showLegalMoves: true,
            playSounds: true,
            premoveEnabled: false,
            autoQueen: true,
            timeControl: 600
        };
        
        const stored = localStorage.getItem('chess-settings');
        return stored ? { ...defaults, ...JSON.parse(stored) } : defaults;
    },
    
    save(settings) {
        localStorage.setItem('chess-settings', JSON.stringify(settings));
    }
};
```

---

### `js/ai.js`
```javascript
// ONNX Model Interface

const PIECE_PLANES = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
};

class AIEngine {
    constructor() {
        this.session = null;
        this.isReady = false;
    }

    async init() {
        try {
            // Try quantized first (faster, smaller)
            this.session = await ort.InferenceSession.create(
                'models/model_quantized.onnx',
                { executionProviders: ['wasm'] }
            );
            console.log('Loaded quantized model');
            this.isReady = true;
        } catch (e) {
            console.warn('Quantized model failed, trying full model:', e);
            try {
                this.session = await ort.InferenceSession.create(
                    'models/model.onnx',
                    { executionProviders: ['wasm'] }
                );
                console.log('Loaded full model');
                this.isReady = true;
            } catch (ee) {
                console.error('Failed to load any ONNX model:', ee);
                throw new Error('Cannot load AI model');
            }
        }
    }

    boardToTensor(chess, clockRatio = 1.0) {
        const tensor = new Float32Array(19 * 8 * 8);
        const board = chess.board();

        // 12 piece planes (white P-K, black p-k)
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = board[row][col];
                if (piece) {
                    const key = piece.color === 'w' ? piece.type.toUpperCase() : piece.type;
                    const plane = PIECE_PLANES[key];
                    const idx = plane * 64 + (7 - row) * 8 + col;
                    tensor[idx] = 1.0;
                }
            }
        }

        // Castling rights (planes 12-15)
        const fen = chess.fen();
        const castling = fen.split(' ')[2];
        if (castling.includes('K')) tensor.fill(1.0, 12 * 64, 13 * 64);
        if (castling.includes('Q')) tensor.fill(1.0, 13 * 64, 14 * 64);
        if (castling.includes('k')) tensor.fill(1.0, 14 * 64, 15 * 64);
        if (castling.includes('q')) tensor.fill(1.0, 15 * 64, 16 * 64);

        // En passant (plane 16)
        const epSquare = fen.split(' ')[3];
        if (epSquare !== '-') {
            const file = 'abcdefgh'.indexOf(epSquare[0]);
            const rank = parseInt(epSquare[1]) - 1;
            tensor[16 * 64 + rank * 8 + file] = 1.0;
        }

        // Turn (plane 17: 1 if white to move)
        if (chess.turn() === 'w') {
            tensor.fill(1.0, 17 * 64, 18 * 64);
        }

        // Clock ratio (plane 18)
        tensor.fill(clockRatio, 18 * 64, 19 * 64);

        return tensor;
    }

    moveToIndex(from, to) {
        const files = 'abcdefgh';
        const fromIdx = files.indexOf(from[0]) + (parseInt(from[1]) - 1) * 8;
        const toIdx = files.indexOf(to[0]) + (parseInt(to[1]) - 1) * 8;
        return fromIdx * 64 + toIdx;
    }

    async predict(chess, clockRatio = 1.0) {
        if (!this.isReady) return null;

        const inputData = this.boardToTensor(chess, clockRatio);
        const inputTensor = new ort.Tensor('float32', inputData, [1, 19, 8, 8]);

        const results = await this.session.run({ board: inputTensor });
        const logits = results.policy_logits.data;

        // Find best legal move
        const legalMoves = chess.moves({ verbose: true });
        if (legalMoves.length === 0) return null;

        let bestMove = null;
        let bestScore = -Infinity;

        for (const move of legalMoves) {
            const idx = this.moveToIndex(move.from, move.to);
            if (logits[idx] > bestScore) {
                bestScore = logits[idx];
                bestMove = move;
            }
        }

        return bestMove;
    }
}
```

---

### `js/game.js`
```javascript
// Chess Game Logic

class ChessGame {
    constructor() {
        this.chess = new Chess();
        this.maxTime = 600; // seconds
        this.timeWhite = 600;
        this.timeBlack = 600;
        this.isRunning = false;
        this.lastTick = 0;
        this.tickInterval = null;
        this.moveHistory = [];
        
        // Sound players
        this.sounds = {
            move: new Audio('sounds/Move.ogg'),
            capture: new Audio('sounds/Capture.ogg'),
            check: new Audio('sounds/Check.ogg'),
            notify: new Audio('sounds/GenericNotify.ogg'),
            lowTime: new Audio('sounds/LowTime.ogg')
        };
        this.playSounds = true;
        this.lowTimePlayed = false;
    }

    reset() {
        this.chess.reset();
        this.timeWhite = this.maxTime;
        this.timeBlack = this.maxTime;
        this.isRunning = false;
        this.lastTick = 0;
        this.moveHistory = [];
        this.lowTimePlayed = false;
        this.stopClock();
    }

    setTimeControl(seconds) {
        this.maxTime = seconds;
        this.timeWhite = seconds;
        this.timeBlack = seconds;
    }

    startClock() {
        if (this.isRunning || this.maxTime === 0) return;
        this.isRunning = true;
        this.lastTick = Date.now();
        
        this.tickInterval = setInterval(() => {
            const now = Date.now();
            const delta = (now - this.lastTick) / 1000;
            this.lastTick = now;

            if (this.chess.turn() === 'w') {
                this.timeWhite = Math.max(0, this.timeWhite - delta);
                if (this.timeWhite === 0) this.onTimeout('white');
                if (this.timeWhite < 10 && !this.lowTimePlayed) {
                    this.playSound('lowTime');
                    this.lowTimePlayed = true;
                }
            } else {
                this.timeBlack = Math.max(0, this.timeBlack - delta);
                if (this.timeBlack === 0) this.onTimeout('black');
            }

            if (this.onClockTick) this.onClockTick();
        }, 100);
    }

    stopClock() {
        if (this.tickInterval) {
            clearInterval(this.tickInterval);
            this.tickInterval = null;
        }
        this.isRunning = false;
    }

    onTimeout(side) {
        this.stopClock();
        this.playSound('notify');
        if (this.onGameOver) {
            this.onGameOver(`Time out! ${side === 'white' ? 'Black' : 'White'} wins.`);
        }
    }

    makeMove(from, to, promotion = 'q') {
        // Start clock on first move
        if (this.chess.history().length === 0 && this.maxTime > 0) {
            this.startClock();
        }

        const moveObj = this.chess.move({ from, to, promotion });
        if (!moveObj) return null;

        this.moveHistory.push(moveObj);

        // Play appropriate sound
        if (this.chess.in_check()) {
            this.playSound('check');
        } else if (moveObj.captured) {
            this.playSound('capture');
        } else {
            this.playSound('move');
        }

        // Check game over
        if (this.chess.game_over()) {
            this.stopClock();
            this.playSound('notify');
            
            let result;
            if (this.chess.in_checkmate()) {
                result = `Checkmate! ${this.chess.turn() === 'w' ? 'Black' : 'White'} wins.`;
            } else if (this.chess.in_draw()) {
                result = 'Draw.';
            } else if (this.chess.in_stalemate()) {
                result = 'Stalemate.';
            } else if (this.chess.in_threefold_repetition()) {
                result = 'Draw by repetition.';
            } else {
                result = 'Game over.';
            }
            
            if (this.onGameOver) this.onGameOver(result);
        }

        return moveObj;
    }

    undo() {
        if (this.chess.history().length < 2) return false;
        this.chess.undo(); // Undo AI move
        this.chess.undo(); // Undo player move
        this.moveHistory.pop();
        this.moveHistory.pop();
        return true;
    }

    playSound(type) {
        if (!this.playSounds) return;
        const sound = this.sounds[type];
        if (sound) {
            sound.currentTime = 0;
            sound.play().catch(() => {});
        }
    }

    getClockRatio() {
        if (this.maxTime === 0) return 1.0;
        return this.chess.turn() === 'b' ? this.timeBlack / this.maxTime : 1.0;
    }

    getTimes() {
        return {
            white: this.timeWhite,
            black: this.timeBlack
        };
    }

    formatTime(seconds) {
        if (this.maxTime === 0) return '∞';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const decisec = Math.floor((seconds % 1) * 10);
        
        if (seconds < 10) {
            return `${mins}:${secs.toString().padStart(2, '0')}.${decisec}`;
        }
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
```

---

### `js/board.js`
```javascript
// Chessground Board Controller

class BoardController {
    constructor(game, ai) {
        this.game = game;
        this.ai = ai;
        this.board = null;
        this.flipped = false;
        this.showLegalMoves = true;
        this.premoveEnabled = false;
        this.autoQueen = true;
    }

    init() {
        const config = {
            fen: this.game.chess.fen(),
            orientation: 'white',
            turnColor: this.toColor(this.game.chess.turn()),
            movable: {
                free: false,
                color: 'white',
                dests: this.getLegalMoves(),
                showDests: this.showLegalMoves,
                events: {
                    after: (orig, dest) => this.onUserMove(orig, dest)
                }
            },
            premovable: {
                enabled: this.premoveEnabled
            },
            draggable: {
                showGhost: true
            },
            highlight: {
                lastMove: true,
                check: true
            },
            animation: {
                enabled: true,
                duration: 200
            },
            events: {
                move: (orig, dest) => {
                    // Arrow drawing could go here
                }
            }
        };

        this.board = Chessground(document.getElementById('board-wrapper'), config);
    }

    toColor(turn) {
        return turn === 'w' ? 'white' : 'black';
    }

    getLegalMoves() {
        const dests = new Map();
        this.game.chess.SQUARES.forEach(sq => {
            const moves = this.game.chess.moves({ square: sq, verbose: true });
            if (moves.length) {
                dests.set(sq, moves.map(m => m.to));
            }
        });
        return dests;
    }

    updateBoard() {
        const turn = this.game.chess.turn();
        this.board.set({
            fen: this.game.chess.fen(),
            turnColor: this.toColor(turn),
            movable: {
                color: turn === 'w' && !this.game.chess.game_over() ? 'white' : undefined,
                dests: this.getLegalMoves(),
                showDests: this.showLegalMoves
            },
            check: this.game.chess.in_check() ? this.toColor(turn) : undefined
        });
    }

    async onUserMove(from, to) {
        let promotion = 'q';
        
        // Check if pawn promotion
        if (!this.autoQueen) {
            const piece = this.game.chess.get(from);
            if (piece && piece.type === 'p') {
                const toRank = parseInt(to[1]);
                if ((piece.color === 'w' && toRank === 8) || (piece.color === 'b' && toRank === 1)) {
                    promotion = prompt('Promote to (q/r/b/n):', 'q') || 'q';
                }
            }
        }

        const move = this.game.makeMove(from, to, promotion);
        if (!move) {
            this.updateBoard(); // Illegal move, reset
            return;
        }

        this.updateBoard();
        if (this.onMove) this.onMove(move);

        // AI's turn
        if (!this.game.chess.game_over() && this.game.chess.turn() === 'b') {
            await this.playAI();
        }
    }

    async playAI() {
        if (this.onAIThinking) this.onAIThinking();

        // Simulate thinking delay
        const ratio = this.game.getClockRatio();
        let thinkTime = 500;
        if (this.game.maxTime > 0) {
            thinkTime = Math.max(100, Math.min(3000, 3000 * ratio * Math.random()));
        }

        await new Promise(r => setTimeout(r, thinkTime));

        const aiMove = await this.ai.predict(this.game.chess, ratio);
        if (aiMove) {
            this.game.makeMove(aiMove.from, aiMove.to, aiMove.promotion || 'q');
            this.updateBoard();
            if (this.onMove) this.onMove(aiMove);
        }

        if (this.onAIDone) this.onAIDone();
    }

    flip() {
        this.flipped = !this.flipped;
        this.board.toggleOrientation();
    }

    setShowLegalMoves(value) {
        this.showLegalMoves = value;
        this.board.set({
            movable: { showDests: value }
        });
    }

    setPremoveEnabled(value) {
        this.premoveEnabled = value;
        this.board.set({
            premovable: { enabled: value }
        });
    }
}
```

---

### `js/ui.js`
```javascript
// UI Controller - wires everything together

(async function() {
    
    // Load settings
    const settings = Config.load();
    
    // Initialize components
    const ai = new AIEngine();
    const game = new ChessGame();
    const board = new BoardController(game, ai);
    
    // DOM elements
    const statusText = document.getElementById('status-text');
    const clockWhite = document.getElementById('clock-white').querySelector('.time');
    const clockBlack = document.getElementById('clock-black').querySelector('.time');
    const moveList = document.getElementById('move-list');
    const timeButtons = document.querySelectorAll('.time-button');
    const btnNewGame = document.getElementById('btn-new-game');
    const btnTakeback = document.getElementById('btn-takeback');
    const btnFlip = document.getElementById('btn-flip');
    const boardThemeSelect = document.getElementById('board-theme');
    const pieceSetSelect = document.getElementById('piece-set');
    const showLegalMovesCheck = document.getElementById('show-legal-moves');
    const playSoundsCheck = document.getElementById('play-sounds');
    const premoveCheck = document.getElementById('premove-enabled');
    const autoQueenCheck = document.getElementById('auto-queen');
    
    // Apply saved settings
    game.setTimeControl(settings.timeControl);
    game.playSounds = settings.playSounds;
    board.showLegalMoves = settings.showLegalMoves;
    board.premoveEnabled = settings.premoveEnabled;
    board.autoQueen = settings.autoQueen;
    
    boardThemeSelect.value = settings.boardTheme;
    pieceSetSelect.value = settings.pieceSet;
    showLegalMovesCheck.checked = settings.showLegalMoves;
    playSoundsCheck.checked = settings.playSounds;
    premoveCheck.checked = settings.premoveEnabled;
    autoQueenCheck.checked = settings.autoQueen;
    
    applyTheme(settings.boardTheme, settings.pieceSet);
    
    // Load AI model
    statusText.textContent = 'Loading AI model...';
    try {
        await ai.init();
        statusText.textContent = 'Ready. Your turn.';
    } catch (e) {
        statusText.textContent = 'Error loading AI model!';
        console.error(e);
        return;
    }
    
    // Initialize board
    board.init();
    
    // Update clocks
    function updateClocks() {
        const times = game.getTimes();
        clockWhite.textContent = game.formatTime(times.white);
        clockBlack.textContent = game.formatTime(times.black);
        
        const whiteEl = document.getElementById('clock-white');
        const blackEl = document.getElementById('clock-black');
        
        whiteEl.classList.toggle('running', game.isRunning && game.chess.turn() === 'w');
        blackEl.classList.toggle('running', game.isRunning && game.chess.turn() === 'b');
        
        whiteEl.classList.toggle('low-time', times.white < 10 && times.white > 0);
        blackEl.classList.toggle('low-time', times.black < 10 && times.black > 0);
    }
    
    game.onClockTick = updateClocks;
    
    // Update move list
    function updateMoveList() {
        const history = game.chess.history({ verbose: true });
        moveList.innerHTML = '';
        
        for (let i = 0; i < history.length; i += 2) {
            const moveNum = Math.floor(i / 2) + 1;
            const white = history[i];
            const black = history[i + 1];
            
            const pair = document.createElement('div');
            pair.className = 'move-pair';
            
            const num = document.createElement('span');
            num.className = 'move-number';
            num.textContent = moveNum + '.';
            
            const whiteSpan = document.createElement('span');
            whiteSpan.className = 'move';
            whiteSpan.textContent = white.san;
            
            pair.appendChild(num);
            pair.appendChild(whiteSpan);
            
            if (black) {
                const blackSpan = document.createElement('span');
                blackSpan.className = 'move';
                blackSpan.textContent = black.san;
                pair.appendChild(blackSpan);
            }
            
            moveList.appendChild(pair);
        }
        
        moveList.scrollTop = moveList.scrollHeight;
    }
    
    board.onMove = () => {
        updateMoveList();
        updateClocks();
    };
    
    board.onAIThinking = () => {
        statusText.textContent = 'AI is thinking...';
    };
    
    board.onAIDone = () => {
        statusText.textContent = game.chess.game_over() ? '' : 'Your turn.';
    };
    
    game.onGameOver = (message) => {
        statusText.textContent = message;
    };
    
    // Event handlers
    btnNewGame.addEventListener('click', () => {
        game.reset();
        board.updateBoard();
        updateClocks();
        moveList.innerHTML = '';
        statusText.textContent = 'Your turn.';
    });
    
    btnTakeback.addEventListener('click', () => {
        if (game.undo()) {
            board.updateBoard();
            updateMoveList();
        }
    });
    
    btnFlip.addEventListener('click', () => {
        board.flip();
    });
    
    timeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const time = parseInt(btn.dataset.time);
            timeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            game.setTimeControl(time);
            game.reset();
            board.updateBoard();
            updateClocks();
            moveList.innerHTML = '';
            statusText.textContent = 'Your turn.';
            
            settings.timeControl = time;
            Config.save(settings);
        });
    });
    
    boardThemeSelect.addEventListener('change', (e) => {
        settings.boardTheme = e.target.value;
        applyTheme(settings.boardTheme, settings.pieceSet);
        Config.save(settings);
    });
    
    pieceSetSelect.addEventListener('change', (e) => {
        settings.pieceSet = e.target.value;
        applyTheme(settings.boardTheme, settings.pieceSet);
        Config.save(settings);
    });
    
    showLegalMovesCheck.addEventListener('change', (e) => {
        settings.showLegalMoves = e.target.checked;
        board.setShowLegalMoves(e.target.checked);
        Config.save(settings);
    });
    
    playSoundsCheck.addEventListener('change', (e) => {
        settings.playSounds = e.target.checked;
        game.playSounds = e.target.checked;
        Config.save(settings);
    });
    
    premoveCheck.addEventListener('change', (e) => {
        settings.premoveEnabled = e.target.checked;
        board.setPremoveEnabled(e.target.checked);
        Config.save(settings);
    });
    
    autoQueenCheck.addEventListener('change', (e) => {
        settings.autoQueen = e.target.checked;
        board.autoQueen = e.target.checked;
        Config.save(settings);
    });
    
    function applyTheme(boardTheme, pieceSet) {
        // Update body class for board theme
        document.body.className = `${boardTheme} ${pieceSet} coords-in`;
        
        // Reload chessground CSS
        const existingLink = document.querySelector('link[href*="chessground."]');
        if (existingLink) {
            const newLink = document.createElement('link');
            newLink.rel = 'stylesheet';
            newLink.href = `https://unpkg.com/@lichess/chessground/assets/chessground.${boardTheme}.css`;
            existingLink.parentNode.insertBefore(newLink, existingLink.nextSibling);
            existingLink.remove();
        }
    }
    
    // Mark active time button on load
    timeButtons.forEach(btn => {
        if (parseInt(btn.dataset.time) === settings.timeControl) {
            btn.classList.add('active');
        }
    });
    
})();
```

---

## 🎨 ADDING MORE FEATURES

### Arrow Drawing (Right-click drag)
Add to `js/board.js` in the board config:
```javascript
drawable: {
    enabled: true,
    visible: true,
    eraseOnClick: true
}
```

### Analysis Mode / Review
Create `js/analysis.js` to step through moves, show engine evaluation, etc.

### Opening Book Display
Parse ECO codes from move history and display opening name.

### Export PGN
```javascript
function exportPGN() {
    const pgn = game.chess.pgn();
    const blob = new Blob([pgn], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'game.pgn';
    a.click();
}
```

---

## 🚀 DEPLOYMENT

### Vercel
```bash
# In your project folder
npm init -y
echo "node_modules" > .gitignore
git init
git add .
git commit -m "Initial commit"

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Netlify
Drag the entire folder into Netlify's web UI. Done.

### GitHub Pages
```bash
git init
git add .
git commit -m "Initial"
git branch -M main
git remote add origin YOUR_REPO_URL
git push -u origin main

# Enable Pages in repo settings → Pages → Source: main branch
```

---

## 🐛 TROUBLESHOOTING

**Board doesn't render:**
- Check browser console for errors
- Verify chessground CSS is loading
- Make sure `board-wrapper` div exists

**ONNX model fails to load:**
- Check file paths (case-sensitive on Linux)
- Verify model files aren't corrupted
- Try running with `--allow-file-access-from-files` flag in Chrome for local testing

**Clocks don't update:**
- Check that `game.onClockTick` callback is set
- Verify interval is running (not blocked by game-over state)

**Sounds don't play:**
- Some browsers block autoplay. User must interact first.
- Check sound file paths
- Verify files downloaded correctly (not 404 HTML pages)

**AI doesn't move:**
- Check browser console for ONNX errors
- Verify model input/output tensor names match (`board`, `policy_logits`)
- Test with a simple position to isolate issues

---

## 📚 REFERENCES

- Lichess source code: https://github.com/lichess-org/lila
- Chessground docs: https://github.com/lichess-org/chessground
- ONNX Runtime Web: https://onnxruntime.ai/docs/tutorials/web/
- Chess.js API: https://github.com/jhlywa/chess.js

---

*Last updated: April 2026 | Ready for deployment*
