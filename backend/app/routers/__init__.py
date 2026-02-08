from app.routers.auth import router as auth_router, get_current_user
from app.routers.game import router as game_router
from app.routers.leaderboard import router as leaderboard_router

__all__ = ["auth_router", "game_router", "leaderboard_router", "get_current_user"]
