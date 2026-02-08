import { useState, useEffect } from 'react';
import { leaderboardAPI } from '../api';
import { useAuth } from '../AuthContext';

interface LeaderboardEntry {
    rank: number;
    username: string;
    points: number;
}

export default function Leaderboard() {
    const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
    const [myRank, setMyRank] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [leaderboardRes, rankRes] = await Promise.all([
                    leaderboardAPI.getLeaderboard(20),
                    leaderboardAPI.getMyRank(),
                ]);
                setEntries(leaderboardRes.data.entries);
                setMyRank(rankRes.data);
            } catch (error) {
                console.error('Failed to fetch leaderboard:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const getRankClass = (rank: number) => {
        if (rank === 1) return 'rank-1';
        if (rank === 2) return 'rank-2';
        if (rank === 3) return 'rank-3';
        return '';
    };

    const getRankEmoji = (rank: number) => {
        if (rank === 1) return '🥇';
        if (rank === 2) return '🥈';
        if (rank === 3) return '🥉';
        return rank;
    };

    if (loading) {
        return (
            <div className="page page-center">
                <div className="matchmaking-spinner"></div>
            </div>
        );
    }

    return (
        <div className="page">
            <div className="container">
                <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>🏆 Leaderboard</h1>

                {/* My Rank Card */}
                {myRank && (
                    <div className="card" style={{ maxWidth: '500px', margin: '0 auto 2rem', textAlign: 'center' }}>
                        <h3>Your Ranking</h3>
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '2rem', marginTop: '1rem' }}>
                            <div>
                                <div style={{ fontSize: '2.5rem', fontWeight: '700' }}>
                                    {myRank.rank ? `#${myRank.rank}` : 'Unranked'}
                                </div>
                                <div style={{ color: 'var(--text-secondary)' }}>Rank</div>
                            </div>
                            <div>
                                <div className="points-badge" style={{ fontSize: '1.5rem', padding: '0.5rem 1rem' }}>
                                    {myRank.points}
                                </div>
                                <div style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Points</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Leaderboard Table */}
                <div className="card" style={{ maxWidth: '700px', margin: '0 auto' }}>
                    {entries.length === 0 ? (
                        <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                            No players yet. Be the first to play!
                        </p>
                    ) : (
                        <table className="leaderboard-table">
                            <thead>
                                <tr>
                                    <th className="rank">Rank</th>
                                    <th>Player</th>
                                    <th style={{ textAlign: 'right' }}>Points</th>
                                </tr>
                            </thead>
                            <tbody>
                                {entries.map((entry) => (
                                    <tr
                                        key={entry.rank}
                                        style={{
                                            background: entry.username === user?.username ? 'rgba(99, 102, 241, 0.1)' : 'transparent'
                                        }}
                                    >
                                        <td className={`rank ${getRankClass(entry.rank)}`}>
                                            {getRankEmoji(entry.rank)}
                                        </td>
                                        <td>
                                            <span style={{ fontWeight: entry.username === user?.username ? '600' : '400' }}>
                                                {entry.username}
                                                {entry.username === user?.username && ' (You)'}
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'right' }}>
                                            <span className="points-badge">{entry.points}</span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}
