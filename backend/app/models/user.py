from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    games_as_white = relationship("Game", foreign_keys="Game.white_player_id", back_populates="white_player")
    games_as_black = relationship("Game", foreign_keys="Game.black_player_id", back_populates="black_player")


class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    black_player_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for bot games
    status = Column(String(20), default="pending")  # pending, active, completed, abandoned
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_bot_game = Column(Boolean, default=False)
    result = Column(String(20), nullable=True)  # white_wins, black_wins, draw
    pgn = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    white_player = relationship("User", foreign_keys=[white_player_id], back_populates="games_as_white")
    black_player = relationship("User", foreign_keys=[black_player_id], back_populates="games_as_black")
    moves = relationship("GameMove", back_populates="game", cascade="all, delete-orphan")


class GameMove(Base):
    __tablename__ = "game_moves"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    move_san = Column(String(10), nullable=False)  # Standard Algebraic Notation
    move_uci = Column(String(10), nullable=False)  # UCI format
    fen_after = Column(String(100), nullable=False)  # Board state after move
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game = relationship("Game", back_populates="moves")
