from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.redis_client import get_redis
from app.models import User, Game, GameMove
from app.schemas import GameResponse, MatchmakingResponse
from app.routers.auth import get_current_user
from app.services import MatchmakingService, create_game, get_game

router = APIRouter(prefix="/game", tags=["Game"])


@router.post("/find-match", response_model=MatchmakingResponse)
async def find_match(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join matchmaking queue and find an opponent or play against bot"""
    redis_client = await get_redis()
    matchmaking = MatchmakingService(redis_client)
    
    result = await matchmaking.find_match(current_user.id, current_user.username)
    
    if result["status"] == "matched":
        # Check if game already exists (Player 2 case - notified about existing game)
        if result.get("game_id") is not None:
            # Game was created by Player 1, just return the info
            return MatchmakingResponse(
                status="matched",
                game_id=result["game_id"],
                opponent=result["opponent_username"],
                color=result["color"]
            )
        
        # Player 1 case - create the game
        db_game = Game(
            white_player_id=current_user.id,  # Initiator is always white
            black_player_id=result["opponent_id"],
            status="active",
            is_bot_game=False
        )
        db.add(db_game)
        await db.commit()
        await db.refresh(db_game)
        
        # Create in-memory game
        create_game(
            game_id=db_game.id,
            white_player_id=db_game.white_player_id,
            black_player_id=db_game.black_player_id,
            is_bot_game=False
        )
        
        # Notify opponent with game_id
        if "other_entry_id" in result:
            await matchmaking.notify_opponent(
                result["other_entry_id"],
                db_game.id,
                current_user.id,
                current_user.username
            )
        
        return MatchmakingResponse(
            status="matched",
            game_id=db_game.id,
            opponent=result["opponent_username"],
            color="white"  # Initiator is always white
        )
    
    elif result["status"] == "bot_game":
        # Create bot game
        db_game = Game(
            white_player_id=current_user.id,
            black_player_id=None,
            status="active",
            is_bot_game=True
        )
        db.add(db_game)
        await db.commit()
        await db.refresh(db_game)
        
        # Create in-memory game
        create_game(
            game_id=db_game.id,
            white_player_id=db_game.white_player_id,
            black_player_id=None,
            is_bot_game=True
        )
        
        return MatchmakingResponse(
            status="bot_game",
            game_id=db_game.id,
            opponent="Stockfish",
            color="white"
        )
    
    return MatchmakingResponse(status="searching")


@router.get("/{game_id}", response_model=GameResponse)
async def get_game_info(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get game details"""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check if user is part of this game
    if game.white_player_id != current_user.id and game.black_player_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this game")
    
    return game


@router.get("/{game_id}/history")
async def get_game_history(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get move history for a game"""
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get moves
    result = await db.execute(
        select(GameMove)
        .where(GameMove.game_id == game_id)
        .order_by(GameMove.move_number)
    )
    moves = result.scalars().all()
    
    # Get in-memory game state if active
    mem_game = get_game(game_id)
    
    return {
        "game_id": game_id,
        "status": game.status,
        "fen": mem_game.get_fen() if mem_game else None,
        "moves": [
            {
                "move_number": m.move_number,
                "move_san": m.move_san,
                "move_uci": m.move_uci,
                "fen_after": m.fen_after
            }
            for m in moves
        ]
    }


@router.get("/{game_id}/state")
async def get_game_state(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current game state"""
    mem_game = get_game(game_id)
    
    if not mem_game:
        raise HTTPException(status_code=404, detail="Game not active")
    
    return {
        "game_id": game_id,
        "fen": mem_game.get_fen(),
        "turn": mem_game.get_current_turn(),
        "legal_moves": mem_game.get_legal_moves(),
        "is_game_over": mem_game.is_game_over(),
        "result": mem_game.get_result() if mem_game.is_game_over() else None
    }
