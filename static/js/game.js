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
        if (this.timeWhite <= 0 || this.timeBlack <= 0) {
            console.log("Move blocked: Time has expired.");
            return null;
        }

        if (this.chess.game_over()) return null;

        if (this.chess.history().length === 0 && this.maxTime > 0) {
            this.startClock();
        }

        const moveObj = this.chess.move({ from, to, promotion });
        if (!moveObj) return null;

        this.moveHistory.push(moveObj);

        if (moveObj.san.includes('#')) {
            // checkmate — notify fires below, skip check sound
        } else if (moveObj.san.includes('+')) {
            this.playSound('check');
        } else if (moveObj.captured) {
            this.playSound('capture');
        } else {
            this.playSound('move');
        }

        if (this.chess.game_over()) {
            this.stopClock();
            this.playSound('notify');

            let result;
            if (this.chess.in_checkmate()) {
                result = `Checkmate! ${this.chess.turn() === 'w' ? 'Black' : 'White'} wins.`;
            } else if (this.chess.in_stalemate()) {
                result = 'Stalemate.';
            } else if (this.chess.in_threefold_repetition()) {
                result = 'Draw by repetition.';
            } else if (this.chess.in_draw()) {
                result = 'Draw.';
            } else {
                result = 'Game over.';
            }

            if (this.onGameOver) setTimeout(() => this.onGameOver(result), 800);
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
            sound.play().catch(() => { });
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