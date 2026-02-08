import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameAPI } from '../api';

export default function Play() {
    const [status, setStatus] = useState<'idle' | 'searching' | 'matched'>('idle');
    const [timer, setTimer] = useState(10);
    const [matchInfo, setMatchInfo] = useState<any>(null);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const findMatch = async () => {
        setStatus('searching');
        setTimer(10);
        setError('');

        try {
            const response = await gameAPI.findMatch();
            const data = response.data;

            if (data.status === 'matched' || data.status === 'bot_game') {
                setStatus('matched');
                setMatchInfo(data);
                // Navigate to game after short delay
                setTimeout(() => {
                    navigate(`/game/${data.game_id}`);
                }, 1500);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to find match');
            setStatus('idle');
        }
    };

    useEffect(() => {
        let interval: any;
        if (status === 'searching' && timer > 0) {
            interval = setInterval(() => {
                setTimer((t) => t - 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [status, timer]);

    return (
        <div className="page page-center">
            <div className="matchmaking-container">
                <div className="card">
                    {status === 'idle' && (
                        <>
                            <h1>Ready to Play?</h1>
                            <p style={{ color: 'var(--text-secondary)', margin: '1rem 0 2rem' }}>
                                Find an opponent or get matched with our AI bot
                            </p>
                            {error && <div className="status-message status-error">{error}</div>}
                            <button className="btn btn-primary btn-large" onClick={findMatch}>
                                🎮 Find Match
                            </button>
                        </>
                    )}

                    {status === 'searching' && (
                        <>
                            <h2>Searching for opponent...</h2>
                            <div className="matchmaking-spinner"></div>
                            <div className="matchmaking-timer">{timer}s</div>
                            <p style={{ color: 'var(--text-secondary)' }}>
                                {timer > 0 ? 'Looking for players...' : 'No players found, matching with bot...'}
                            </p>
                        </>
                    )}

                    {status === 'matched' && matchInfo && (
                        <>
                            <h2 style={{ color: 'var(--success)' }}>Match Found!</h2>
                            <div style={{ fontSize: '4rem', margin: '1.5rem 0' }}>⚔️</div>
                            <p style={{ fontSize: '1.25rem' }}>
                                Playing against: <strong>{matchInfo.opponent}</strong>
                            </p>
                            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                                You are playing as <strong style={{ color: matchInfo.color === 'white' ? '#fff' : '#888' }}>
                                    {matchInfo.color}
                                </strong>
                            </p>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
