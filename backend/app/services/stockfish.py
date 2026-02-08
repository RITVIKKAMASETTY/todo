from stockfish import Stockfish
from typing import Optional
from app.config import get_settings

settings = get_settings()


class StockfishService:
    _instance: Optional[Stockfish] = None
    
    @classmethod
    def get_engine(cls) -> Optional[Stockfish]:
        """Get or create Stockfish instance"""
        if cls._instance is None:
            try:
                cls._instance = Stockfish(
                    path=settings.STOCKFISH_PATH,
                    depth=settings.STOCKFISH_DEPTH,
                    parameters={
                        "Threads": 2,
                        "Minimum Thinking Time": 30
                    }
                )
            except Exception as e:
                print(f"Failed to initialize Stockfish: {e}")
                return None
        return cls._instance
    
    @classmethod
    def get_best_move(cls, fen: str) -> Optional[str]:
        """Get the best move for the current position"""
        engine = cls.get_engine()
        if engine is None:
            # Fallback: return a random legal move
            return cls._get_random_move(fen)
        
        try:
            engine.set_fen_position(fen)
            return engine.get_best_move()
        except Exception as e:
            print(f"Stockfish error: {e}")
            return cls._get_random_move(fen)
    
    @classmethod
    def _get_random_move(cls, fen: str) -> Optional[str]:
        """Fallback: get a random legal move using python-chess"""
        import chess
        import random
        
        board = chess.Board(fen)
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves).uci()
        return None
    
    @classmethod
    def set_difficulty(cls, depth: int):
        """Adjust bot difficulty by changing search depth"""
        engine = cls.get_engine()
        if engine:
            engine.set_depth(depth)
    
    @classmethod
    def evaluate_position(cls, fen: str) -> Optional[dict]:
        """Evaluate the current position"""
        engine = cls.get_engine()
        if engine is None:
            return None
        
        try:
            engine.set_fen_position(fen)
            evaluation = engine.get_evaluation()
            return evaluation
        except Exception:
            return None
