import json
import asyncio
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.redis_client import get_redis
from app.models import User, Game, GameMove
from app.services import get_game, remove_game, StockfishService, update_points
from app.config import get_settings

settings = get_settings()


class ConnectionManager:
    """Manages WebSocket connections for games"""
    
    def __init__(self):
        # game_id -> {user_id: websocket}
        self.active_connections: dict[int, dict[int, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: int, user_id: int):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][user_id] = websocket
    
    def disconnect(self, game_id: int, user_id: int):
        if game_id in self.active_connections:
            if user_id in self.active_connections[game_id]:
                del self.active_connections[game_id][user_id]
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
    
    async def send_to_game(self, game_id: int, message: dict):
        """Send message to all players in a game"""
        if game_id in self.active_connections:
            for websocket in self.active_connections[game_id].values():
                try:
                    await websocket.send_json(message)
                except:
                    pass
    
    async def send_to_player(self, game_id: int, user_id: int, message: dict):
        """Send message to a specific player"""
        if game_id in self.active_connections:
            if user_id in self.active_connections[game_id]:
                try:
                    await self.active_connections[game_id][user_id].send_json(message)
                except:
                    pass


manager = ConnectionManager()


async def handle_game_websocket(websocket: WebSocket, game_id: int, user_id: int):
    """Main WebSocket handler for chess games"""
    
    # Get game from memory
    game = get_game(game_id)
    if not game:
        await websocket.close(code=4004, reason="Game not found")
        return
    
    # Verify user is part of this game
    if user_id != game.white_player_id and user_id != game.black_player_id:
        await websocket.close(code=4003, reason="Not authorized")
        return
    
    # Connect
    await manager.connect(websocket, game_id, user_id)
    
    # Determine player color
    player_color = "white" if user_id == game.white_player_id else "black"
    
    # Send initial state
    await websocket.send_json({
        "type": "game_state",
        "game_id": game_id,
        "fen": game.get_fen(),
        "turn": game.get_current_turn(),
        "your_color": player_color,
        "legal_moves": game.get_legal_moves() if game.get_current_turn() == player_color else [],
        "is_bot_game": game.is_bot_game
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            await process_message(websocket, game_id, user_id, player_color, data)
    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        # Notify opponent of disconnect
        await manager.send_to_game(game_id, {
            "type": "opponent_disconnected",
            "message": f"{player_color} player disconnected"
        })


async def process_message(websocket: WebSocket, game_id: int, user_id: int, player_color: str, data: dict):
    """Process incoming WebSocket messages"""
    
    game = get_game(game_id)
    if not game:
        await websocket.send_json({"type": "error", "message": "Game not found"})
        return
    
    msg_type = data.get("type")
    
    if msg_type == "move":
        await handle_move(websocket, game_id, user_id, player_color, data.get("move"))
    
    elif msg_type == "resign":
        await handle_resign(game_id, user_id, player_color)
    
    elif msg_type == "get_state":
        await websocket.send_json({
            "type": "game_state",
            "fen": game.get_fen(),
            "turn": game.get_current_turn(),
            "legal_moves": game.get_legal_moves() if game.get_current_turn() == player_color else []
        })


async def handle_move(websocket: WebSocket, game_id: int, user_id: int, player_color: str, move_uci: str):
    """Handle a chess move"""
    
    game = get_game(game_id)
    if not game:
        return
    
    # Check if it's player's turn
    if game.get_current_turn() != player_color:
        await websocket.send_json({
            "type": "error",
            "message": "Not your turn"
        })
        return
    
    # Make the move
    result = game.make_move(move_uci)
    
    if not result["success"]:
        await websocket.send_json({
            "type": "error",
            "message": result.get("error", "Invalid move")
        })
        return
    
    # Save move to database
    async with AsyncSessionLocal() as db:
        db_move = GameMove(
            game_id=game_id,
            move_number=len(game.move_history),
            move_san=result["move_san"],
            move_uci=result["move_uci"],
            fen_after=result["fen"]
        )
        db.add(db_move)
        await db.commit()
    
    # Broadcast move to all players
    await manager.send_to_game(game_id, {
        "type": "move",
        "move_san": result["move_san"],
        "move_uci": result["move_uci"],
        "fen": result["fen"],
        "turn": game.get_current_turn(),
        "is_game_over": result["is_game_over"],
        "result": result.get("result")
    })
    
    # Check if game is over
    if result["is_game_over"]:
        await handle_game_end(game_id, result["result"])
        return
    
    # If bot game, make bot move
    if game.is_bot_game and game.get_current_turn() == "black":
        await asyncio.sleep(0.5)  # Small delay for UX
        await make_bot_move(game_id)


async def make_bot_move(game_id: int):
    """Make a move for the Stockfish bot"""
    
    game = get_game(game_id)
    if not game or game.is_game_over():
        return
    
    # Get best move from Stockfish
    bot_move = StockfishService.get_best_move(game.get_fen())
    
    if not bot_move:
        # Fallback: resign if no move found
        await handle_game_end(game_id, "white_wins")
        return
    
    # Make the move
    result = game.make_move(bot_move)
    
    if result["success"]:
        # Save to database
        async with AsyncSessionLocal() as db:
            db_move = GameMove(
                game_id=game_id,
                move_number=len(game.move_history),
                move_san=result["move_san"],
                move_uci=result["move_uci"],
                fen_after=result["fen"]
            )
            db.add(db_move)
            await db.commit()
        
        # Broadcast
        await manager.send_to_game(game_id, {
            "type": "move",
            "move_san": result["move_san"],
            "move_uci": result["move_uci"],
            "fen": result["fen"],
            "turn": game.get_current_turn(),
            "is_game_over": result["is_game_over"],
            "result": result.get("result"),
            "is_bot_move": True
        })
        
        if result["is_game_over"]:
            await handle_game_end(game_id, result["result"])


async def handle_resign(game_id: int, user_id: int, player_color: str):
    """Handle player resignation"""
    
    winner = "black_wins" if player_color == "white" else "white_wins"
    
    await manager.send_to_game(game_id, {
        "type": "game_over",
        "result": winner,
        "reason": "resignation"
    })
    
    await handle_game_end(game_id, winner)


async def handle_game_end(game_id: int, result: str):
    """Handle end of game - update database and points"""
    
    game = get_game(game_id)
    if not game:
        return
    
    async with AsyncSessionLocal() as db:
        # Update game in database
        db_game_result = await db.execute(select(Game).where(Game.id == game_id))
        db_game = db_game_result.scalar_one_or_none()
        
        if db_game:
            db_game.status = "completed"
            db_game.result = result
            db_game.completed_at = datetime.now(timezone.utc)
            db_game.pgn = game.get_pgn()
            
            # Determine winner
            if result == "white_wins":
                db_game.winner_id = db_game.white_player_id
            elif result == "black_wins" and db_game.black_player_id:
                db_game.winner_id = db_game.black_player_id
            
            await db.commit()
        
        # Update points
        redis_client = await get_redis()
        
        # Get players
        white_result = await db.execute(select(User).where(User.id == game.white_player_id))
        white_player = white_result.scalar_one_or_none()
        
        if white_player:
            if result == "white_wins":
                white_player.points += settings.WIN_POINTS
                await update_points(redis_client, white_player.id, white_player.username, settings.WIN_POINTS)
            elif result == "draw":
                white_player.points += settings.DRAW_POINTS
                await update_points(redis_client, white_player.id, white_player.username, settings.DRAW_POINTS)
        
        if game.black_player_id:
            black_result = await db.execute(select(User).where(User.id == game.black_player_id))
            black_player = black_result.scalar_one_or_none()
            
            if black_player:
                if result == "black_wins":
                    black_player.points += settings.WIN_POINTS
                    await update_points(redis_client, black_player.id, black_player.username, settings.WIN_POINTS)
                elif result == "draw":
                    black_player.points += settings.DRAW_POINTS
                    await update_points(redis_client, black_player.id, black_player.username, settings.DRAW_POINTS)
        
        await db.commit()
    
    # Broadcast game over
    await manager.send_to_game(game_id, {
        "type": "game_over",
        "result": result,
        "white_points": settings.WIN_POINTS if result == "white_wins" else (settings.DRAW_POINTS if result == "draw" else 0),
        "black_points": settings.WIN_POINTS if result == "black_wins" else (settings.DRAW_POINTS if result == "draw" else 0)
    })
    
    # Remove from active games
    remove_game(game_id)
