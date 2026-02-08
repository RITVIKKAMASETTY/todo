from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    points: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None


# Game Schemas
class GameCreate(BaseModel):
    pass


class GameResponse(BaseModel):
    id: int
    white_player_id: int
    black_player_id: Optional[int]
    status: str
    is_bot_game: bool
    result: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class GameMoveCreate(BaseModel):
    move: str  # UCI format like "e2e4"


class GameMoveResponse(BaseModel):
    id: int
    move_number: int
    move_san: str
    move_uci: str
    fen_after: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Matchmaking Schemas
class MatchmakingResponse(BaseModel):
    status: str  # searching, matched, bot_game
    game_id: Optional[int] = None
    opponent: Optional[str] = None
    color: Optional[str] = None


# Leaderboard Schemas
class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    points: int


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total_players: int
