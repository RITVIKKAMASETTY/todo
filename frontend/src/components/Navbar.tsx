import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Navbar() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="navbar">
            <div className="container navbar-content">
                <Link to="/" className="nav-brand">♟️ Chess Arena</Link>

                <div className="nav-links">
                    {user ? (
                        <>
                            <Link to="/play" className="nav-link">Play</Link>
                            <Link to="/leaderboard" className="nav-link">Leaderboard</Link>
                            <span style={{ color: 'var(--text-secondary)' }}>
                                {user.username} • <span className="points-badge">{user.points}</span>
                            </span>
                            <button className="btn btn-secondary" onClick={handleLogout}>
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="nav-link">Login</Link>
                            <Link to="/register" className="btn btn-primary">Sign Up</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
}
