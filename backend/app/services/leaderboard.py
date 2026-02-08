import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

LEADERBOARD_KEY = "chess:leaderboard"


async def add_to_leaderboard(redis_client: redis.Redis, user_id: int, username: str, points: int):
    """Add or update user in leaderboard"""
    # Use sorted set with score = points, member = "user_id:username"
    member = f"{user_id}:{username}"
    await redis_client.zadd(LEADERBOARD_KEY, {member: points})


async def update_points(redis_client: redis.Redis, user_id: int, username: str, points_delta: int):
    """Update user's points in leaderboard"""
    member = f"{user_id}:{username}"
    await redis_client.zincrby(LEADERBOARD_KEY, points_delta, member)


async def get_top_players(redis_client: redis.Redis, limit: int = 10) -> list[dict]:
    """Get top N players from leaderboard"""
    results = await redis_client.zrevrange(LEADERBOARD_KEY, 0, limit - 1, withscores=True)
    leaderboard = []
    for rank, (member, score) in enumerate(results, start=1):
        user_id, username = member.split(":", 1)
        leaderboard.append({
            "rank": rank,
            "user_id": int(user_id),
            "username": username,
            "points": int(score)
        })
    return leaderboard


async def get_player_rank(redis_client: redis.Redis, user_id: int, username: str) -> dict | None:
    """Get a specific player's rank"""
    member = f"{user_id}:{username}"
    rank = await redis_client.zrevrank(LEADERBOARD_KEY, member)
    if rank is None:
        return None
    score = await redis_client.zscore(LEADERBOARD_KEY, member)
    return {
        "rank": rank + 1,  # Convert 0-indexed to 1-indexed
        "user_id": user_id,
        "username": username,
        "points": int(score) if score else 0
    }


async def get_total_players(redis_client: redis.Redis) -> int:
    """Get total number of players in leaderboard"""
    return await redis_client.zcard(LEADERBOARD_KEY)
