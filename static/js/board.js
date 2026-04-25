// Chessground Board Controller

class BoardController {
    constructor(game, ai) {
        this.game = game;
        this.ai = ai;
        this.board = null;
        this.flipped = false;
        this.showLegalMoves = true;
        this.autoQueen = true;
        this.playerSide = 'white';
    }

    setPlayerSide(side) {
        this.playerSide = side;
        this.flipped = side === 'black';
    }

    init() {
        const config = {
            fen: this.game.chess.fen(),
            orientation: this.playerSide,
            turnColor: this.toColor(this.game.chess.turn()),
            movable: {
                free: false,
                color: this.game.chess.turn() === this.playerSide[0] ? this.playerSide : undefined,
                dests: this.getLegalMoves(),
                showDests: this.showLegalMoves,
                events: {
                    after: (orig, dest) => this.onUserMove(orig, dest)
                }
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
            },
            drawable: {
                enabled: true,
                visible: true,
                eraseOnClick: true
            }
        };

        this.board = window.Chessground(document.getElementById('board-wrapper'), config);
    }

    destroy() {
        if (this.board && typeof this.board.destroy === 'function') {
            this.board.destroy();
        }
        const wrapper = document.getElementById('board-wrapper');
        if (wrapper) {
            wrapper.innerHTML = '';
            wrapper.className = 'cg-wrap'; // Reset to base class
        }
        this.board = null;
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
            orientation: this.playerSide,
            turnColor: this.toColor(turn),
            movable: {
                color: (turn === this.playerSide[0] && !this.game.chess.game_over()) ? this.playerSide : undefined,
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
        if (!this.game.chess.game_over() && this.game.chess.turn() !== this.playerSide[0]) {
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
}