import chess
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ChessGame:
    """Manages the state of a chess game"""
    game_id: int
    white_player_id: int
    black_player_id: Optional[int]  # None for bot games
    is_bot_game: bool = False
    board: chess.Board = field(default_factory=chess.Board)
    move_history: list = field(default_factory=list)
    
    def make_move(self, move_uci: str) -> dict:
        """
        Attempt to make a move.
        Returns dict with success status and game state.
        """
        try:
            move = chess.Move.from_uci(move_uci)
            
            if move not in self.board.legal_moves:
                return {
                    "success": False,
                    "error": "Illegal move"
                }
            
            # Get SAN before making move
            move_san = self.board.san(move)
            
            # Make the move
            self.board.push(move)
            
            # Record move
            move_number = len(self.move_history) + 1
            self.move_history.append({
                "move_number": move_number,
                "move_san": move_san,
                "move_uci": move_uci,
                "fen_after": self.board.fen()
            })
            
            return {
                "success": True,
                "move_san": move_san,
                "move_uci": move_uci,
                "fen": self.board.fen(),
                "is_game_over": self.is_game_over(),
                "result": self.get_result() if self.is_game_over() else None
            }
            
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid move format: {str(e)}"
            }
    
    def is_game_over(self) -> bool:
        """Check if the game is over"""
        return self.board.is_game_over()
    
    def get_result(self) -> Optional[str]:
        """Get the game result"""
        if not self.is_game_over():
            return None
        
        if self.board.is_checkmate():
            # The side that just moved won
            if self.board.turn == chess.WHITE:
                return "black_wins"
            else:
                return "white_wins"
        elif self.board.is_stalemate():
            return "draw"
        elif self.board.is_insufficient_material():
            return "draw"
        elif self.board.is_fifty_moves():
            return "draw"
        elif self.board.is_repetition():
            return "draw"
        return "draw"
    
    def get_current_turn(self) -> str:
        """Get whose turn it is"""
        return "white" if self.board.turn == chess.WHITE else "black"
    
    def get_legal_moves(self) -> list[str]:
        """Get all legal moves in UCI format"""
        return [move.uci() for move in self.board.legal_moves]
    
    def get_fen(self) -> str:
        """Get current board position in FEN notation"""
        return self.board.fen()
    
    def get_pgn(self) -> str:
        """Get game in PGN format"""
        import chess.pgn
        import io
        
        game = chess.pgn.Game()
        node = game
        
        temp_board = chess.Board()
        for move_data in self.move_history:
            move = chess.Move.from_uci(move_data["move_uci"])
            node = node.add_variation(move)
            temp_board.push(move)
        
        exporter = io.StringIO()
        exporter.write(str(game))
        return exporter.getvalue()


# In-memory game storage (for active games)
active_games: dict[int, ChessGame] = {}


def create_game(game_id: int, white_player_id: int, black_player_id: Optional[int], is_bot_game: bool = False) -> ChessGame:
    """Create a new game and store it"""
    game = ChessGame(
        game_id=game_id,
        white_player_id=white_player_id,
        black_player_id=black_player_id,
        is_bot_game=is_bot_game
    )
    active_games[game_id] = game
    return game


def get_game(game_id: int) -> Optional[ChessGame]:
    """Get an active game by ID"""
    return active_games.get(game_id)


def remove_game(game_id: int):
    """Remove a game from active games"""
    if game_id in active_games:
        del active_games[game_id]
