from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import get_redis
from app.models import User
from app.schemas import LeaderboardEntry, LeaderboardResponse
from app.routers.auth import get_current_user
from app.services import get_top_players, get_player_rank, get_total_players

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get top players leaderboard"""
    redis_client = await get_redis()
    
    top_players = await get_top_players(redis_client, limit)
    total = await get_total_players(redis_client)
    
    entries = [
        LeaderboardEntry(
            rank=p["rank"],
            username=p["username"],
            points=p["points"]
        )
        for p in top_players
    ]
    
    return LeaderboardResponse(entries=entries, total_players=total)


@router.get("/me")
async def get_my_rank(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's rank"""
    redis_client = await get_redis()
    
    rank_info = await get_player_rank(redis_client, current_user.id, current_user.username)
    
    if not rank_info:
        return {
            "rank": None,
            "username": current_user.username,
            "points": current_user.points,
            "message": "Not ranked yet"
        }
    
    return {
        "rank": rank_info["rank"],
        "username": current_user.username,
        "points": rank_info["points"]
    }
