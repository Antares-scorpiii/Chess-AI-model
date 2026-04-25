// ONNX Model Interface - Supports both behavioral and Maia models
 
const PIECE_PLANES = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
};
 
// Maia policy index mapping (1858 legal moves)
// This is a subset - full map would be loaded from external file
// For now we'll compute it on the fly
const MAIA_MOVE_MAP = null; // Will be generated if needed
 
class AIEngine {
    constructor() {
        this.session = null;
        this.isReady = false;
        this.config = null;
        this.encoding = 'from_to_64x64';
        this.maiaPolicyIndex = null;
        this.maiaIndexToMove = null; // Reverse mapping
    }
 
    async init() {
        // Load model config
        try {
            const response = await fetch('model_config.json');
            this.config = await response.json();
            this.encoding = this.config.encoding || 'from_to_64x64';
            console.log('Loaded model config:', this.config);
        } catch (e) {
            console.warn('Could not load model_config.json, using defaults');
            this.config = {
                model_type: 'behavioral',
                model_path: 'behavioral_model/model.onnx',
                quantized_path: 'behavioral_model/model_quantized.onnx',
                encoding: 'from_to_64x64'
            };
        }
 
        // If Maia model, load policy index
        if (this.encoding === 'maia_policy_1858') {
            await this.loadMaiaPolicyIndex();
        }
 
        // Try to load quantized first, fallback to full
        try {
            this.session = await ort.InferenceSession.create(
                this.config.quantized_path,
                { executionProviders: ['wasm'] }
            );
            console.log(`Loaded quantized ${this.config.model_type} model`);
            this.isReady = true;
        } catch (e) {
            console.warn('Quantized model failed, trying full model:', e);
            try {
                this.session = await ort.InferenceSession.create(
                    this.config.model_path,
                    { executionProviders: ['wasm'] }
                );
                console.log(`Loaded full ${this.config.model_type} model`);
                this.isReady = true;
            } catch (ee) {
                console.error('Failed to load any ONNX model:', ee);
                throw new Error('Cannot load AI model');
            }
        }
    }
 
    async switchModel(configPath) {
        this.isReady = false;
        const response = await fetch(configPath);
        this.config = await response.json();
        this.encoding = this.config.encoding || 'from_to_64x64';

        if (this.encoding === 'maia_policy_1858' && !this.maiaPolicyIndex) {
            await this.loadMaiaPolicyIndex();
        }

        try {
            this.session = await ort.InferenceSession.create(
                this.config.quantized_path,
                { executionProviders: ['wasm'] }
            );
        } catch (e) {
            console.warn('Quantized model failed, trying full model:', e);
            this.session = await ort.InferenceSession.create(
                this.config.model_path,
                { executionProviders: ['wasm'] }
            );
        }
        this.isReady = true;
    }

    async loadMaiaPolicyIndex() {
        try {
            const response = await fetch('maia_model/maia_policy_index.json');
            this.maiaPolicyIndex = await response.json();
            
            // Build reverse mapping: move string -> index
            this.maiaIndexToMove = {};
            for (const [moveStr, idx] of Object.entries(this.maiaPolicyIndex)) {
                this.maiaIndexToMove[idx] = moveStr;
            }
            
            console.log('Loaded Maia policy index:', Object.keys(this.maiaPolicyIndex).length, 'moves');
        } catch (e) {
            console.error('Failed to load Maia policy index:', e);
            throw new Error('Cannot load Maia policy index - required for Maia model');
        }
    }
 
    boardToTensor(chess) {
        return this.encoding === 'maia_policy_1858'
            ? this._maiaBoard(chess)
            : this._behavioralBoard(chess);
    }

    _behavioralBoard(chess) {
        // Matches board_to_tensor() in src/core/data/features.py
        const tensor = new Float32Array(19 * 8 * 8);
        const board = chess.board();
        const PLANES = { P:0, N:1, B:2, R:3, Q:4, K:5, p:6, n:7, b:8, r:9, q:10, k:11 };

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = board[row][col];
                if (!piece) continue;
                const key = piece.color === 'w' ? piece.type.toUpperCase() : piece.type;
                tensor[PLANES[key] * 64 + (7 - row) * 8 + col] = 1.0;
            }
        }

        const parts = chess.fen().split(' ');
        const castling = parts[2];
        if (castling.includes('K')) tensor.fill(1.0, 12 * 64, 13 * 64);
        if (castling.includes('Q')) tensor.fill(1.0, 13 * 64, 14 * 64);
        if (castling.includes('k')) tensor.fill(1.0, 14 * 64, 15 * 64);
        if (castling.includes('q')) tensor.fill(1.0, 15 * 64, 16 * 64);
        tensor.fill(chess.turn() === 'w' ? 1.0 : 0.0, 16 * 64, 17 * 64);
        tensor.fill(parseInt(parts[4]) / 100, 17 * 64, 18 * 64);
        return tensor;
    }

    _maiaBoard(chess) {
        // Matches board_to_maia_tensor() in src/core/data/features.py exactly.
        // Python uses board.mirror() for black: rank-flip (same file) + color swap.
        // For black: chess.js (row, col) → python tensor index (row, col) — no file flip.
        // For white: chess.js row 0=rank8 → python rank 7, so sqIdx = (7-row)*8 + col.
        const tensor = new Float32Array(112 * 8 * 8);
        const isBlack = chess.turn() === 'b';
        const board = chess.board();
        const typeMap = { p: 0, n: 1, b: 2, r: 3, q: 4, k: 5 };

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = board[row][col];
                if (!piece) continue;
                const isOwn = piece.color === chess.turn();
                const plane = (isOwn ? 0 : 6) + typeMap[piece.type];
                const sqIdx = isBlack ? row * 8 + col : (7 - row) * 8 + col;
                tensor[plane * 64 + sqIdx] = 1.0;
            }
        }

        // Plane 12: always 1.0 (Lc0 constant)
        tensor.fill(1.0, 12 * 64, 13 * 64);

        const parts = chess.fen().split(' ');
        const castling = parts[2];

        // Planes 104-107: castling — own KS, own QS, opp KS, opp QS
        const [ownK, ownQ, oppK, oppQ] = isBlack ? ['k', 'q', 'K', 'Q'] : ['K', 'Q', 'k', 'q'];
        if (castling.includes(ownK)) tensor.fill(1.0, 104 * 64, 105 * 64);
        if (castling.includes(ownQ)) tensor.fill(1.0, 105 * 64, 106 * 64);
        if (castling.includes(oppK)) tensor.fill(1.0, 106 * 64, 107 * 64);
        if (castling.includes(oppQ)) tensor.fill(1.0, 107 * 64, 108 * 64);

        // Plane 108: always 1.0 (side-to-move, always current player's view)
        tensor.fill(1.0, 108 * 64, 109 * 64);

        // Plane 109: 50-move rule
        tensor.fill(parseInt(parts[4]) / 100, 109 * 64, 110 * 64);

        // Plane 111: always 1.0
        tensor.fill(1.0, 111 * 64, 112 * 64);

        return tensor;
    }
 
    moveToIndex64x64(from, to) {
        const files = 'abcdefgh';
        const fromIdx = files.indexOf(from[0]) + (parseInt(from[1]) - 1) * 8;
        const toIdx = files.indexOf(to[0]) + (parseInt(to[1]) - 1) * 8;
        return fromIdx * 64 + toIdx;
    }
 
    moveToUCI(move) {
        // Convert chess.js move to UCI string
        let uci = move.from + move.to;
        if (move.promotion) {
            uci += move.promotion;
        }
        return uci;
    }
 
    getMaiaMoveIndex(move, isBlack) {
        // Matches move_to_maia_index() in src/core/data/features.py.
        // For black, mirror ranks (chess.square_mirror flips rank, same file): rank r → (9-r).
        let from = move.from, to = move.to;
        if (isBlack) {
            const mir = sq => sq[0] + String(9 - parseInt(sq[1]));
            from = mir(move.from);
            to = mir(move.to);
        }
        let uci = from + to + (move.promotion || '');
        if (uci.endsWith('n')) uci = uci.slice(0, -1); // Lc0 drops knight promotion suffix

        if (this.maiaPolicyIndex && this.maiaPolicyIndex[uci] !== undefined) {
            return this.maiaPolicyIndex[uci];
        }
        console.warn('Move not in Maia policy index:', uci);
        return -1;
    }
 
    async predict(chess) {
        if (!this.isReady) return null;
 
        const inputData = this.boardToTensor(chess);
        const isMaia = this.encoding === 'maia_policy_1858';
        const shape = isMaia ? [1, 112, 8, 8] : [1, 19, 8, 8];
        const inputTensor = new ort.Tensor('float32', inputData, shape);

        const results = await this.session.run({ board: inputTensor });
        const logits = results.policy_logits.data;

        const legalMoves = chess.moves({ verbose: true });
        if (legalMoves.length === 0) return null;

        let bestMove = null;
        let bestScore = -Infinity;

        if (!isMaia) {
            for (const move of legalMoves) {
                const idx = this.moveToIndex64x64(move.from, move.to);
                if (idx < logits.length && logits[idx] > bestScore) {
                    bestScore = logits[idx];
                    bestMove = move;
                }
            }
        } else {
            const isBlack = chess.turn() === 'b';
            for (const move of legalMoves) {
                const idx = this.getMaiaMoveIndex(move, isBlack);
                if (idx >= 0 && idx < logits.length && logits[idx] > bestScore) {
                    bestScore = logits[idx];
                    bestMove = move;
                }
            }
        }
 
        return bestMove;
    }
}