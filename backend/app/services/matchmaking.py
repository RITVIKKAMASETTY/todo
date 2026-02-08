import asyncio
import uuid
import redis.asyncio as redis
from typing import Optional
from app.config import get_settings

settings = get_settings()

MATCHMAKING_QUEUE = "chess:matchmaking:queue"
MATCHMAKING_RESULTS = "chess:matchmaking:results:"


class MatchmakingService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.timeout = settings.MATCHMAKING_TIMEOUT_SECONDS
    
    async def join_queue(self, user_id: int, username: str) -> str:
        """Add player to matchmaking queue and return their queue entry ID"""
        entry_id = str(uuid.uuid4())
        entry = f"{user_id}:{username}:{entry_id}"
        
        # Add to queue
        await self.redis.lpush(MATCHMAKING_QUEUE, entry)
        
        return entry_id
    
    async def find_match(self, user_id: int, username: str) -> dict:
        """
        Try to find a match for the player.
        Returns match result after timeout or when match is found.
        """
        entry_id = await self.join_queue(user_id, username)
        result_key = f"{MATCHMAKING_RESULTS}{entry_id}"
        
        # Wait for match result (check every 500ms)
        elapsed = 0
        check_interval = 0.5
        
        while elapsed < self.timeout:
            # Check if matched by another player
            result = await self.redis.get(result_key)
            if result:
                await self.redis.delete(result_key)
                parts = result.split(":")
                return {
                    "status": "matched",
                    "game_id": int(parts[0]),
                    "opponent_id": int(parts[1]),
                    "opponent_username": parts[2],
                    "color": parts[3]
                }
            
            # Try to match with someone else in queue
            match_result = await self._try_match(user_id, username, entry_id)
            if match_result:
                return match_result
            
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        
        # Timeout - remove from queue and return bot game
        await self._remove_from_queue(user_id, username, entry_id)
        return {
            "status": "bot_game",
            "game_id": None,  # Will be created by caller
            "opponent_id": None,
            "opponent_username": "Stockfish",
            "color": "white"
        }
    
    async def _try_match(self, user_id: int, username: str, entry_id: str) -> Optional[dict]:
        """Try to find and match with another player in queue using atomic operations"""
        
        # Use atomic RPOP to get one entry from queue
        # This prevents race conditions where both players try to match simultaneously
        while True:
            entry = await self.redis.rpop(MATCHMAKING_QUEUE)
            if not entry:
                # Queue is empty, re-add ourselves
                return None
            
            other_user_id, other_username, other_entry_id = entry.split(":")
            other_user_id = int(other_user_id)
            
            # Don't match with self - put it back and continue
            if other_user_id == user_id:
                # Put our entry back at the end
                await self.redis.rpush(MATCHMAKING_QUEUE, entry)
                return None
            
            # Remove ourselves from queue as well
            await self._remove_from_queue(user_id, username, entry_id)
            
            # Found a match! (this player is white, other is black)
            return {
                "status": "matched",
                "game_id": None,  # Will be created by caller
                "opponent_id": other_user_id,
                "opponent_username": other_username,
                "color": "white",
                "other_entry_id": other_entry_id
            }
    
    async def notify_opponent(self, other_entry_id: str, game_id: int, user_id: int, username: str):
        """Notify the matched opponent about the game"""
        result_key = f"{MATCHMAKING_RESULTS}{other_entry_id}"
        result = f"{game_id}:{user_id}:{username}:black"
        await self.redis.setex(result_key, 30, result)  # Expire after 30 seconds
    
    async def _remove_from_queue(self, user_id: int, username: str, entry_id: str):
        """Remove a player from the matchmaking queue"""
        entry = f"{user_id}:{username}:{entry_id}"
        await self.redis.lrem(MATCHMAKING_QUEUE, 0, entry)
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        return await self.redis.llen(MATCHMAKING_QUEUE)
