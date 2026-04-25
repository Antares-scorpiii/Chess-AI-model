import chess.pgn
import numpy as np
import os
import argparse
import yaml
from tqdm import tqdm
from src.core.data.features import board_to_maia_tensor, move_to_maia_index

def prepare_maia_data(input_pgn, output_dir, username=None, max_games=None):
    os.makedirs(output_dir, exist_ok=True)
    
    boards = []
    moves = []
    
    game_count = 0
    with open(input_pgn) as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
                
            player_color = None
            if username:
                if game.headers.get("White") == username:
                    player_color = chess.WHITE
                elif game.headers.get("Black") == username:
                    player_color = chess.BLACK
                else:
                    continue

            board = game.board()
            for move in game.mainline_moves():
                if player_color is None or board.turn == player_color:
                    planes = board_to_maia_tensor(board)
                    move_idx = move_to_maia_index(move, board)
                    
                    if move_idx is not None:
                        boards.append(planes)
                        moves.append(move_idx)
                
                board.push(move)
            
            game_count += 1
            if max_games and game_count >= max_games:
                break
            
            if game_count % 100 == 0:
                print(f"Processed {game_count} games...")
    
    print(f"Total positions captured for {username or 'all players'}: {len(boards)}")
    
    boards = np.array(boards, dtype=np.float16)
    moves = np.array(moves, dtype=np.int64)
    
    output_path = os.path.join(output_dir, "training_data.npz")
    np.savez(output_path, boards=boards, moves=moves)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--username", help="Target player username to filter moves")
    parser.add_argument("--max_games", type=int, default=None)
    parser.add_argument("--config", help="Path to config.yaml to get username")
    args = parser.parse_args()
    
    username = args.username
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
            username = config.get("username", username)
    
    prepare_maia_data(args.input, args.output, username, args.max_games)
