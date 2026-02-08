import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import type { Square } from 'chess.js';
import { useAuth } from '../AuthContext';

type PromotionPiece = 'q' | 'r' | 'b' | 'n';

// --- Components ---

const CapturedPieces = ({ history }: { history: string[], myColor: 'white' | 'black' }) => {
    // Calculate captured pieces based on move history
    const getCapturedPieces = () => {
        const game = new Chess();
        const captured = { w: [] as string[], b: [] as string[] };

        for (const move of history) {
            try {
                const moveResult = game.move(move);
                if (moveResult && moveResult.captured) {
                    // If white moved and captured, it captured a black piece
                    if (moveResult.color === 'w') {
                        captured.b.push(moveResult.captured);
                    } else {
                        captured.w.push(moveResult.captured);
                    }
                }
            } catch (e) {
                console.error("Error replaying move for capture calculation:", e);
            }
        }
        return captured;
    };

    const captured = getCapturedPieces();

    // Material values
    const values: Record<string, number> = { p: 1, n: 3, b: 3, r: 5, q: 9 };

    const calculateMaterial = (pieces: string[]) => pieces.reduce((acc, p) => acc + (values[p] || 0), 0);
    const whiteMaterial = calculateMaterial(captured.b); // White captured black pieces
    const blackMaterial = calculateMaterial(captured.w); // Black captured white pieces

    const whiteAdvantage = whiteMaterial - blackMaterial;

    const renderPieces = (pieces: string[], color: 'w' | 'b') => (
        <div className="captured-row">
            {pieces.map((p, i) => (
                <span key={i} className={`captured-piece piece-${color}${p}`}>
                    {getPieceSymbol(p)}
                </span>
            ))}
            {/* Show advantage */}
            {color === 'w' && whiteAdvantage > 0 && <span className="material-advantage">+{whiteAdvantage}</span>}
            {color === 'b' && whiteAdvantage < 0 && <span className="material-advantage">+{Math.abs(whiteAdvantage)}</span>}
        </div>
    );

    const getPieceSymbol = (piece: string) => {
        const symbols: Record<string, string> = {
            p: '♟', n: '♞', b: '♝', r: '♜', q: '♛'
        };
        // We always use the "black" filled symbols for better visibility, colored by CSS
        return symbols[piece] || '';
    };

    return (
        <div className="captured-pieces-container">
            <div className="captured-group">
                {renderPieces(captured.b, 'w')} {/* White captured these (black) */}
            </div>
            <div className="captured-group">
                {renderPieces(captured.w, 'b')} {/* Black captured these (white) */}
            </div>
        </div>
    );
};

const MoveHistory = ({ moves }: { moves: string[] }) => {
    const movePairs = [];
    for (let i = 0; i < moves.length; i += 2) {
        movePairs.push({
            number: Math.floor(i / 2) + 1,
            white: moves[i],
            black: moves[i + 1] || ''
        });
    }

    return (
        <div className="move-history-scroll">
            <table className="move-history-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>White</th>
                        <th>Black</th>
                    </tr>
                </thead>
                <tbody>
                    {movePairs.map((pair) => (
                        <tr key={pair.number}>
                            <td className="move-number">{pair.number}.</td>
                            <td className="move-white">{pair.white}</td>
                            <td className="move-black">{pair.black}</td>
                        </tr>
                    ))}
                    <tr ref={(el) => el?.scrollIntoView({ behavior: 'smooth' })}></tr>
                </tbody>
            </table>
        </div>
    );
};

// --- Main Game Component ---

export default function Game() {
    const { gameId } = useParams();
    const { token, user } = useAuth();
    const navigate = useNavigate();

    const [game, setGame] = useState(new Chess());
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [myColor, setMyColor] = useState<'white' | 'black'>('white');
    const [isMyTurn, setIsMyTurn] = useState(false);
    const [gameOver, setGameOver] = useState(false);
    const [result, setResult] = useState('');
    const [isBotGame, setIsBotGame] = useState(false);
    const [moveHistory, setMoveHistory] = useState<string[]>([]);

    // Legal move highlighting
    const [selectedSquare, setSelectedSquare] = useState<Square | null>(null);
    const [legalMoves, setLegalMoves] = useState<Square[]>([]);

    // Pawn promotion
    const [showPromotionDialog, setShowPromotionDialog] = useState(false);
    const [pendingPromotion, setPendingPromotion] = useState<{ from: string, to: string } | null>(null);

    // Check/Checkmate indicators
    const [isInCheck, setIsInCheck] = useState(false);

    // Use ref to track myColor for use in WebSocket callback
    const myColorRef = useRef(myColor);
    useEffect(() => {
        myColorRef.current = myColor;
    }, [myColor]);

    // Connect to WebSocket
    useEffect(() => {
        if (!gameId || !token) return;

        const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}?token=${token}`);

        ws.onopen = () => {
            console.log('Connected to game');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('Disconnected from game');
        };

        setSocket(ws);

        return () => {
            ws.close();
        };
    }, [gameId, token]);

    const handleServerMessage = useCallback((data: any) => {
        console.log('Server message:', data);

        switch (data.type) {
            case 'game_state':
                const newGame = new Chess(data.fen);
                setGame(newGame);
                setMyColor(data.your_color);
                myColorRef.current = data.your_color;
                setIsMyTurn(data.turn === data.your_color);
                setIsBotGame(data.is_bot_game);
                setIsInCheck(newGame.inCheck());

                // Reconstruct move history if needed (simplified here, in real app we might fetch full history)
                // For now, we assume history is empty on load or handled elsewhere if we want persistence
                break;

            case 'move':
                setGame(() => {
                    const updated = new Chess(data.fen);
                    setIsInCheck(updated.inCheck());
                    return updated;
                });
                setMoveHistory((prev) => [...prev, data.move_san]);
                setIsMyTurn(data.turn === myColorRef.current);
                setSelectedSquare(null);
                setLegalMoves([]);

                if (data.is_game_over) {
                    setGameOver(true);
                    setResult(data.result);
                }
                break;

            case 'game_over':
                setGameOver(true);
                setResult(data.result);
                break;

            case 'opponent_disconnected':
                alert('Opponent disconnected');
                break;

            case 'error':
                console.error('Game error:', data.message);
                break;
        }
    }, []);

    // Get legal moves for a piece
    const getLegalMovesForSquare = (square: Square): Square[] => {
        const moves = game.moves({ square, verbose: true });
        return moves.map(move => move.to as Square);
    };

    // Handle square click for move highlighting
    const onSquareClick = (square: Square) => {
        if (!isMyTurn || gameOver) return;

        // If clicking on a piece of our color
        const piece = game.get(square);
        if (piece && piece.color === (myColor === 'white' ? 'w' : 'b')) {
            setSelectedSquare(square);
            setLegalMoves(getLegalMovesForSquare(square));
            return;
        }

        // If we have a selected piece and clicking on valid target
        if (selectedSquare && legalMoves.includes(square)) {
            makeMove(selectedSquare, square);
        } else {
            setSelectedSquare(null);
            setLegalMoves([]);
        }
    };

    // Check if move is a pawn promotion
    const isPromotion = (from: string, to: string): boolean => {
        try {
            const piece = game.get(from as Square);
            if (!piece || piece.type !== 'p') return false;

            const toRank = parseInt(to[1]);
            return (piece.color === 'w' && toRank === 8) || (piece.color === 'b' && toRank === 1);
        } catch {
            return false;
        }
    };

    // Make a move
    const makeMove = (from: string, to: string, promotion: PromotionPiece = 'q') => {
        try {
            // Check if this is a promotion
            if (isPromotion(from, to) && !showPromotionDialog) {
                setPendingPromotion({ from, to });
                setShowPromotionDialog(true);
                return;
            }

            const gameCopy = new Chess(game.fen());
            const move = gameCopy.move({
                from,
                to,
                promotion,
            });

            if (!move) return;

            // Send move to server (include promotion piece if applicable)
            const moveStr = promotion && isPromotion(from, to)
                ? `${from}${to}${promotion}`
                : `${from}${to}`;

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    type: 'move',
                    move: moveStr,
                }));
            }

            setSelectedSquare(null);
            setLegalMoves([]);
        } catch (error) {
            console.log('Invalid move attempted:', from, to);
        }
    };

    // Handle promotion selection
    const handlePromotion = (piece: PromotionPiece) => {
        if (pendingPromotion) {
            makeMove(pendingPromotion.from, pendingPromotion.to, piece);
        }
        setShowPromotionDialog(false);
        setPendingPromotion(null);
    };

    const onDrop = useCallback((args: any) => {
        const { sourceSquare, targetSquare } = args;
        if (!isMyTurn || gameOver) return false;

        try {
            // Check if this is a promotion
            if (isPromotion(sourceSquare, targetSquare)) {
                setPendingPromotion({ from: sourceSquare, to: targetSquare });
                setShowPromotionDialog(true);
                return true; // Accept the drop, will complete after promotion choice
            }

            const gameCopy = new Chess(game.fen());
            const move = gameCopy.move({
                from: sourceSquare,
                to: targetSquare,
                promotion: 'q',
            });

            if (!move) return false;

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    type: 'move',
                    move: `${sourceSquare}${targetSquare}`,
                }));
            }

            setSelectedSquare(null);
            setLegalMoves([]);
            return true;
        } catch (error) {
            console.log('Invalid move attempted:', sourceSquare, targetSquare);
            return false;
        }
    }, [game, isMyTurn, gameOver, socket]);

    const resign = () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'resign' }));
        }
    };

    const getResultMessage = () => {
        if (!result) return '';
        if (result === 'draw') return "It's a draw!";
        const winner = result === 'white_wins' ? 'White' : 'Black';
        const isWinner = (result === 'white_wins' && myColor === 'white') ||
            (result === 'black_wins' && myColor === 'black');
        return isWinner ? '🎉 You won!' : `${winner} wins`;
    };

    // Generate square styles for highlighting
    const getSquareStyles = () => {
        const styles: { [key: string]: React.CSSProperties } = {};

        // Highlight selected square
        if (selectedSquare) {
            styles[selectedSquare] = {
                backgroundColor: 'rgba(255, 235, 59, 0.5)',
            };
        }

        // Highlight legal move squares
        legalMoves.forEach(square => {
            const piece = game.get(square);
            styles[square] = {
                background: piece
                    ? 'radial-gradient(circle, transparent 60%, rgba(255, 0, 0, 0.5) 60%)'  // Capture (red ring)
                    : 'radial-gradient(circle, rgba(0, 255, 0, 0.4) 25%, transparent 25%)', // Empty (green dot)
            };
        });

        // Highlight king in check
        if (isInCheck && !gameOver) {
            const kingSquare = findKingSquare();
            if (kingSquare) {
                styles[kingSquare] = {
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    boxShadow: '0 0 15px rgba(239, 68, 68, 0.8)'
                };
            }
        }

        // Highlight last move
        const lastMove = game.history({ verbose: true }).pop();
        if (lastMove) {
            styles[lastMove.from] = { backgroundColor: 'rgba(99, 102, 241, 0.3)' };
            styles[lastMove.to] = { backgroundColor: 'rgba(99, 102, 241, 0.3)' };
        }

        return styles;
    };

    // Find the king's square for check highlighting
    const findKingSquare = (): Square | null => {
        const board = game.board();
        const kingColor = game.turn();

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = board[row][col];
                if (piece && piece.type === 'k' && piece.color === kingColor) {
                    const files = 'abcdefgh';
                    return `${files[col]}${8 - row}` as Square;
                }
            }
        }
        return null;
    };

    return (
        <div className="page display-flex flex-center">
            <div className="container game-layout">
                {/* Left Panel: Players & Board */}
                <div className="board-section">

                    {/* Opponent Card */}
                    <div className={`player-card glass-panel ${!isMyTurn && !gameOver ? 'active-turn' : ''} ${gameOver && result.includes(myColor === 'white' ? 'white' : 'black') ? 'winner' : ''}`}>
                        <div className="player-info">
                            <div className="player-avatar" style={{ background: myColor === 'white' ? '#333' : 'var(--accent-gradient)' }}>
                                {isBotGame ? '🤖' : 'O'}
                            </div>
                            <div className="player-details">
                                <div className="player-name">{isBotGame ? 'Stockfish Bot' : 'Opponent'}</div>
                                <div className="player-status">
                                    {isBotGame ? 'Level 10' : 'Rank: 1200'}
                                </div>
                            </div>
                        </div>
                        <CapturedPieces history={moveHistory} myColor={myColor === 'white' ? 'black' : 'white'} />
                    </div>

                    {/* Chess Board */}
                    <div className="board-wrapper">
                        <Chessboard
                            options={{
                                position: game.fen(),
                                onPieceDrop: onDrop,
                                onSquareClick: (args: any) => onSquareClick(args.square),
                                boardOrientation: myColor,
                                boardStyle: {
                                    borderRadius: '12px',
                                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
                                },
                                darkSquareStyle: { backgroundColor: '#4f46e5' }, // Indigo-600
                                lightSquareStyle: { backgroundColor: '#eef2ff' }, // Indigo-50
                                squareStyles: getSquareStyles(),
                            }}
                        />

                        {/* Check Indicator Overlay */}
                        {isInCheck && !gameOver && (
                            <div className="check-indicator">
                                ⚠️ CHECK!
                            </div>
                        )}

                        {/* Promotion Dialog */}
                        {showPromotionDialog && (
                            <div className="promotion-dialog">
                                <div className="promotion-content glass-panel">
                                    <h3>Promote to...</h3>
                                    <div className="promotion-pieces">
                                        <button onClick={() => handlePromotion('q')} title="Queen">♛</button>
                                        <button onClick={() => handlePromotion('r')} title="Rook">♜</button>
                                        <button onClick={() => handlePromotion('b')} title="Bishop">♝</button>
                                        <button onClick={() => handlePromotion('n')} title="Knight">♞</button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* My Player Card */}
                    <div className={`player-card glass-panel ${isMyTurn && !gameOver ? 'active-turn' : ''} ${gameOver && !result.includes(myColor === 'white' ? 'black' : 'white') ? 'winner' : ''}`}>
                        <div className="player-info">
                            <div className="player-avatar">
                                {user?.username.charAt(0).toUpperCase()}
                            </div>
                            <div className="player-details">
                                <div className="player-name">{user?.username}</div>
                                <div className="player-status">
                                    Points: {user?.points || 0}
                                </div>
                            </div>
                        </div>
                        <CapturedPieces history={moveHistory} myColor={myColor} />
                    </div>
                </div>

                {/* Right Panel: Game Info & History */}
                <div className="sidebar-section">
                    <div className="glass-panel sidebar-content">
                        <div className="game-header">
                            <h2>Chess Match</h2>
                            <div className="game-meta">
                                <span className="meta-badge">{isBotGame ? 'vs Bot' : 'Rated'}</span>
                                <span className="meta-badge">10 min</span>
                            </div>
                        </div>

                        {/* Status / Turn */}
                        {!gameOver ? (
                            <div className={`turn-banner ${isMyTurn ? 'green' : 'amber'}`}>
                                {isMyTurn ? "Your turn to move" : "Waiting for opponent..."}
                            </div>
                        ) : (
                            <div className="game-over-banner">
                                <div className="result-icon">
                                    {result === 'draw' ? '🤝' : (
                                        ((result === 'white_wins' && myColor === 'white') ||
                                            (result === 'black_wins' && myColor === 'black')) ? '🏆' : '👑'
                                    )}
                                </div>
                                <h3>{getResultMessage()}</h3>
                                <p>
                                    {game.isCheckmate() ? 'by Checkmate' :
                                        game.isStalemate() ? 'by Stalemate' :
                                            game.isDraw() ? 'by Draw' : 'Game Over'}
                                </p>
                                <button className="btn btn-primary full-width" onClick={() => navigate('/')}>
                                    Return to Home
                                </button>
                            </div>
                        )}

                        {/* Move History */}
                        <div className="history-container">
                            <h4>Move History</h4>
                            <MoveHistory moves={moveHistory} />
                        </div>

                        {/* Actions */}
                        {!gameOver && (
                            <div className="action-buttons">
                                <button className="btn btn-secondary full-width" onClick={resign}>
                                    🏳️ Resign Game
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

