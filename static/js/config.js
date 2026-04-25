// Settings persistence (localStorage)

const Config = {
    load() {
        const defaults = {
            showLegalMoves: true,
            playSounds: true,
            autoQueen: true,
            darkMode: true,
            timeControl: 600,
            playerSide: 'white'
        };

        const stored = localStorage.getItem('chess-settings');
        return stored ? { ...defaults, ...JSON.parse(stored) } : defaults;
    },

    save(settings) {
        localStorage.setItem('chess-settings', JSON.stringify(settings));
    }
};