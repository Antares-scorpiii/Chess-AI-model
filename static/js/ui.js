// UI Controller - wires everything together
window.addEventListener('load', async () => {
    // Load settings
    const settings = Config.load();
    console.log("Settings loaded:", settings);

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
    const showLegalMovesCheck = document.getElementById('show-legal-moves');
    const playSoundsCheck = document.getElementById('play-sounds');
    const autoQueenCheck = document.getElementById('auto-queen');
    const themeBtn = document.getElementById('theme-btn');
    const themeIcon = document.getElementById('theme-icon');

    const sunPath = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
    const moonPath = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';

    function applyTheme(darkMode) {
        document.body.classList.toggle('theme-dark', darkMode);
        document.body.classList.toggle('theme-light', !darkMode);
        themeIcon.innerHTML = darkMode ? moonPath : sunPath;
    }

    // Update clock labels based on player side
    function updateClockLabels() {
        const aiLabel = document.querySelector('.ruser .username');
        const playerLabel = document.querySelector('.ruser:last-child .username');
        
        if (board.playerSide === 'white') {
            aiLabel.textContent = 'AI Agent';
            playerLabel.textContent = 'You';
        } else {
            aiLabel.textContent = 'You';
            playerLabel.textContent = 'AI Agent';
        }
    }

    // Game history tracking
    let gameHistory = [];
    const gameHistoryContainer = document.createElement('div');
    gameHistoryContainer.className = 'game-history';
    gameHistoryContainer.innerHTML = '<div class="history-header">User vs Aniruddh\'s Bot</div><div class="history-tally">Wins: 0 | Losses: 0 | Draws: 0</div><div class="history-list"></div>';
    
    // Insert game history above settings
    const leftPanel = document.querySelector('.left-panel');
    leftPanel.insertBefore(gameHistoryContainer, leftPanel.firstChild);

    function updateGameHistory(result, playerSide, pgn) {
        gameHistory.push({
            result: result,
            playerSide: playerSide,
            pgn: pgn,
            timestamp: new Date()
        });

        // Update tally
        const wins = gameHistory.filter(g => g.result === 'win').length;
        const losses = gameHistory.filter(g => g.result === 'loss').length;
        const draws = gameHistory.filter(g => g.result === 'draw').length;

        gameHistoryContainer.querySelector('.history-tally').textContent = `Wins: ${wins} | Losses: ${losses} | Draws: ${draws}`;

        // Add to list
        const list = gameHistoryContainer.querySelector('.history-list');
        const gameItem = document.createElement('div');
        gameItem.className = 'history-item';

        const resultText = document.createElement('span');
        resultText.textContent = `${playerSide === 'white' ? 'White' : 'Black'}: ${result === 'win' ? 'Won' : result === 'loss' ? 'Lost' : 'Draw'}`;

        const pgnLink = document.createElement('button');
        pgnLink.className = 'pgn-download-btn';
        pgnLink.textContent = 'PGN';
        pgnLink.onclick = () => {
            const blob = new Blob([pgn], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `game_${gameHistory.length}.pgn`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        };

        gameItem.appendChild(resultText);
        gameItem.appendChild(pgnLink);
        list.appendChild(gameItem);
        list.scrollTop = list.scrollHeight;
    }

    // Apply saved settings
    game.setTimeControl(settings.timeControl);
    game.playSounds = settings.playSounds;
    board.showLegalMoves = settings.showLegalMoves;
    board.autoQueen = settings.autoQueen;
    board.setPlayerSide(settings.playerSide);
    updateClockLabels(); // Set initial clock labels

    showLegalMovesCheck.checked = settings.showLegalMoves;
    playSoundsCheck.checked = settings.playSounds;
    autoQueenCheck.checked = settings.autoQueen;
    applyTheme(settings.darkMode);

    themeBtn.addEventListener('click', () => {
        settings.darkMode = !settings.darkMode;
        applyTheme(settings.darkMode);
        Config.save(settings);
        themeBtn.classList.add('spin');
        themeBtn.addEventListener('transitionend', () => themeBtn.classList.remove('spin'), { once: true });
    });

    // Initialize board FIRST so it appears immediately
    board.init();
    console.log("Board Controller initialized");

    const modelBtns = document.querySelectorAll('.model-btn');

    function updateActiveModelBtn() {
        const activeConfig = ai.config && ai.config.model_type === 'maia'
            ? 'model_config_maia.json'
            : 'model_config_behavior.json';
        modelBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.config === activeConfig);
        });
    }

    console.log("Attempting to init AI...");
    statusText.textContent = 'Loading AI model...';
    try {
        await ai.init();
        console.log("AI Init complete");
        updateActiveModelBtn();
        statusText.textContent = 'Ready. Your turn.';
    } catch (e) {
        statusText.textContent = 'Error loading AI model!';
        console.error("AI Init failed!", e);
    }

    modelBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            if (btn.classList.contains('active')) return;
            statusText.textContent = 'Switching model...';
            try {
                await ai.switchModel(btn.dataset.config);
                updateActiveModelBtn();
                statusText.textContent = 'Ready. Your turn.';
            } catch (e) {
                statusText.textContent = 'Error loading model!';
                console.error('Model switch failed:', e);
            }
        });
    });

    // Update clocks
    function updateClocks() {
        const times = game.getTimes();
        
        // Display times based on player side
        if (board.playerSide === 'white') {
            clockWhite.textContent = game.formatTime(times.white); // Player's time
            clockBlack.textContent = game.formatTime(times.black); // AI's time
        } else {
            clockWhite.textContent = game.formatTime(times.black); // Player's time  
            clockBlack.textContent = game.formatTime(times.white); // AI's time
        }

        const whiteEl = document.getElementById('clock-white');
        const blackEl = document.getElementById('clock-black');

        // Running indicators based on whose turn it is
        const isPlayerTurn = game.chess.turn() === board.playerSide[0];
        whiteEl.classList.toggle('running', game.isRunning && isPlayerTurn); // Player's clock
        blackEl.classList.toggle('running', game.isRunning && !isPlayerTurn); // AI's clock

        // Low time indicators
        if (board.playerSide === 'white') {
            whiteEl.classList.toggle('low-time', times.white < 10 && times.white > 0);
            blackEl.classList.toggle('low-time', times.black < 10 && times.black > 0);
        } else {
            whiteEl.classList.toggle('low-time', times.black < 10 && times.black > 0);
            blackEl.classList.toggle('low-time', times.white < 10 && times.white > 0);
        }
    }

    function updateStatus() {
        if (game.chess.game_over()) {
            return; // Let game over handler set the message
        }

        const currentTurn = game.chess.turn();
        const isPlayerTurn = currentTurn === board.playerSide[0];

        if (isPlayerTurn) {
            statusText.textContent = 'Your turn.';
        } else {
            statusText.textContent = 'AI is thinking...';
        }
    }

    game.onClockTick = updateClocks;

    // Update move list with full logic from guide
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
            whiteSpan.onclick = () => { /* Future: Jump to position */ };

            pair.appendChild(num);
            pair.appendChild(whiteSpan);

            if (black) {
                const blackSpan = document.createElement('span');
                blackSpan.className = 'move';
                blackSpan.textContent = black.san;
                blackSpan.onclick = () => { /* Future: Jump to position */ };
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
        updateStatus();
    };

    game.onGameOver = (message) => {
        // Determine winner and record result
        let result = 'draw';
        let dialogMessage = 'Draw! Play another?';

        if (message.includes('Black wins') || message.includes('White wins')) {
            const isPlayerWinner = (board.playerSide === 'white' && message.includes('White wins')) ||
                                 (board.playerSide === 'black' && message.includes('Black wins'));
            result = isPlayerWinner ? 'win' : 'loss';
            dialogMessage = isPlayerWinner ? 'You Win GG! Wish to play again?' : 'Good Game! Wish to play again?';
        }

        updateGameHistory(result, board.playerSide, game.chess.pgn());

        if (confirm(dialogMessage)) {
            const newSide = board.playerSide === 'white' ? 'black' : 'white';
            const time = settings.timeControl;

            game.setTimeControl(time);
            game.reset();
            board.setPlayerSide(newSide);
            if (board.board && typeof board.board.cancelMove === 'function') {
                board.board.cancelMove();
            }
            board.init();
            updateClockLabels();
            updateClocks();
            moveList.innerHTML = '';
            updateStatus();

            // Update active button
            timeButtons.forEach(btn => {
                if (parseInt(btn.dataset.time) === time && btn.dataset.side === newSide) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });

            settings.playerSide = newSide;
            Config.save(settings);

            // If new side is black, AI moves first
            if (newSide === 'black' && !game.chess.game_over()) {
                board.playAI();
            }
        }
        // If user cancels, just update status
        else {
            statusText.textContent = message;
        }
    };

    // Event handlers
    btnNewGame.addEventListener('click', () => {
        // Check if game is ongoing
        if (game.chess.history().length > 0 && !game.chess.game_over()) {
            if (!confirm('Game is currently ongoing. Do you want to quit this game?')) {
                return;
            }
        }

        // Randomly select one of the 6 time control options
        const timeControls = [
            { time: 180, side: 'white' }, // 3+0 White
            { time: 180, side: 'black' }, // 3+0 Black
            { time: 300, side: 'white' }, // 5+0 White
            { time: 300, side: 'black' }, // 5+0 Black
            { time: 600, side: 'white' }, // 10+0 White
            { time: 600, side: 'black' }  // 10+0 Black
        ];
        const randomIndex = Math.floor(Math.random() * timeControls.length);
        const selectedControl = timeControls[randomIndex];

        // Set the selected time control and side
        game.setTimeControl(selectedControl.time);
        board.setPlayerSide(selectedControl.side);
        updateClockLabels();

        // Update active button
        timeButtons.forEach(btn => {
            if (parseInt(btn.dataset.time) === selectedControl.time && btn.dataset.side === selectedControl.side) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        settings.timeControl = selectedControl.time;
        settings.playerSide = selectedControl.side;
        Config.save(settings);

        game.reset();
        board.updateBoard();
        updateClocks();
        moveList.innerHTML = '';
        updateStatus();

        // If player is black, AI moves first
        if (selectedControl.side === 'black' && !game.chess.game_over()) {
            board.playAI();
        }
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
            // Check if game is ongoing
            if (game.chess.history().length > 0 && !game.chess.game_over()) {
                if (!confirm('Game is currently ongoing. Do you want to quit this game?')) {
                    return;
                }
            }

            const time = parseInt(btn.dataset.time);
            const side = btn.dataset.side;
            timeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            game.setTimeControl(time);
            game.reset();
            board.setPlayerSide(side);
            // Cancel any pending moves before reinitializing
            if (board.board && typeof board.board.cancelMove === 'function') {
                board.board.cancelMove();
            }
            board.init(); // Reinitialize board for clean state
            updateClockLabels(); // Update clock labels for new side
            updateClocks();
            moveList.innerHTML = '';
            updateStatus();

            settings.timeControl = time;
            settings.playerSide = side;
            Config.save(settings);

            // If player is black, AI moves first
            if (side === 'black' && !game.chess.game_over()) {
                board.playAI();
            }
        });
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

    autoQueenCheck.addEventListener('change', (e) => {
        settings.autoQueen = e.target.checked;
        board.autoQueen = e.target.checked;
        Config.save(settings);
    });

    // Mark active time button on load
    timeButtons.forEach(btn => {
        if (parseInt(btn.dataset.time) === settings.timeControl && btn.dataset.side === settings.playerSide) {
            btn.classList.add('active');
        }
    });
});