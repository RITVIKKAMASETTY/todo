import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Dashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();

    return (
        <div className="page">
            <div className="container">
                <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                    <h1>Welcome, {user?.username}!</h1>
                    <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                        Your Points: <span className="points-badge">{user?.points || 0}</span>
                    </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', maxWidth: '900px', margin: '0 auto' }}>
                    {/* Play Card */}
                    <div className="card" style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>♟️</div>
                        <h3>Play Chess</h3>
                        <p style={{ color: 'var(--text-secondary)', margin: '1rem 0' }}>
                            Find an opponent or play against the bot
                        </p>
                        <button className="btn btn-primary btn-large" onClick={() => navigate('/play')}>
                            Find Match
                        </button>
                    </div>

                    {/* Leaderboard Card */}
                    <div className="card" style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏆</div>
                        <h3>Leaderboard</h3>
                        <p style={{ color: 'var(--text-secondary)', margin: '1rem 0' }}>
                            See the top players and your ranking
                        </p>
                        <button className="btn btn-secondary btn-large" onClick={() => navigate('/leaderboard')}>
                            View Rankings
                        </button>
                    </div>

                    {/* Stats Card */}
                    <div className="card" style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
                        <h3>Your Stats</h3>
                        <p style={{ color: 'var(--text-secondary)', margin: '1rem 0' }}>
                            Total Points: {user?.points || 0}
                        </p>
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                            <div>
                                <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--success)' }}>
                                    {Math.floor((user?.points || 0) / 10)}
                                </div>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Wins</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
