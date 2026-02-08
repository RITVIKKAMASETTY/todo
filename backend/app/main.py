from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError

from app.config import get_settings
from app.database import init_db
from app.redis_client import get_redis, close_redis
from app.routers import auth_router, game_router, leaderboard_router
from app.websocket import handle_game_websocket

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await get_redis()  # Initialize Redis connection
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time multiplayer chess backend with matchmaking and leaderboard",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(game_router)
app.include_router(leaderboard_router)


@app.get("/")
async def root():
    return {
        "message": "Chess Backend API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    redis = await get_redis()
    redis_ok = await redis.ping()
    return {
        "status": "healthy",
        "redis": "connected" if redis_ok else "disconnected"
    }


@app.websocket("/ws/game/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: int,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time chess gameplay"""
    
    # Verify token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        # Convert to int (JWT stores sub as string)
        user_id = int(user_id)
    except (JWTError, ValueError):
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Handle game WebSocket
    await handle_game_websocket(websocket, game_id, user_id)
