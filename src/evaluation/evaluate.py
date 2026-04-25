import chess.engine

def evaluate_centipawn_loss(model_moves, reference_moves, fen_positions, engine_path):
    """
    Compare model moves vs your actual moves using Stockfish evaluation.
    Lower centipawn loss = model plays more like you (or better than you).
    """
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    
    model_losses, player_losses = [], []
    
    for fen, model_move, player_move in zip(fen_positions, model_moves, reference_moves):
        board = chess.Board(fen)
        
        best = engine.analyse(board, chess.engine.Limit(depth=15))
        best_score = best["score"].relative.score(mate_score=10000)
        
        board.push(model_move)
        model_eval = engine.analyse(board, chess.engine.Limit(depth=15))
        model_score = model_eval["score"].relative.score(mate_score=10000)
        board.pop()
        
        board.push(player_move)
        player_eval = engine.analyse(board, chess.engine.Limit(depth=15))
        player_score = player_eval["score"].relative.score(mate_score=10000)
        board.pop()
        
        if best_score is not None and model_score is not None and player_score is not None:
            model_losses.append(max(0, best_score - model_score))
            player_losses.append(max(0, best_score - player_score))
    
    engine.quit()
    
    if len(model_losses) > 0:
        print(f"Model avg centipawn loss:  {sum(model_losses)/len(model_losses):.1f}")
        print(f"Player avg centipawn loss: {sum(player_losses)/len(player_losses):.1f}")

if __name__ == "__main__":
    import argparse
    import yaml
    import torch
    import sys
    import numpy as np
    from tqdm import tqdm
    
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.core.data.parse import parse_games
    from src.core.data.features import board_to_tensor, move_to_index, index_to_move
    from src.core.model.chess_net import ChessNet
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--samples", type=int, default=100)
    args = parser.parse_args()
    
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading model on {device} for Centipawn evaluation...")
    
    model = ChessNet(channels=config["channels"], num_res_blocks=config["num_res_blocks"]).to(device)
    model.load_state_dict(torch.load(config["checkpoint_path"], map_location=device))
    model.eval()
    
    print(f"Extracting {args.samples} positions from {config['pgn_path']}...")
    fen_positions = []
    reference_moves = []
    model_moves = []
    
    try:
        iterator = parse_games(config["pgn_path"], config["username"])
    except FileNotFoundError:
        print(f"Error: {config['pgn_path']} not found. Run 'make download' first.")
        sys.exit(1)
        
    count = 0
    for board, player_move, clock_ratio, result in iterator:
        if count >= args.samples:
            break
            
        fen_positions.append(board.fen())
        reference_moves.append(player_move)
        
        board_tensor = torch.tensor(board_to_tensor(board, clock_ratio)).unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(board_tensor)[0].cpu().numpy()
            
        legal_move_indices = {move_to_index(m) for m in board.legal_moves}
        masked_logits = np.full(4096, -float('inf'))
        for legal_idx in legal_move_indices:
            masked_logits[legal_idx] = logits[legal_idx]
            
        ai_move = index_to_move(int(np.argmax(masked_logits)), board=board)
        model_moves.append(ai_move)
        
        count += 1
        
    print(f"Feeding {count} positions to Stockfish for Centipawn analysis...")
    engine_path = config.get("engine_path", "/usr/bin/stockfish")
    if not os.path.exists(engine_path):
        engine_path = "/usr/games/stockfish"
        
    evaluate_centipawn_loss(model_moves, reference_moves, fen_positions, engine_path)
