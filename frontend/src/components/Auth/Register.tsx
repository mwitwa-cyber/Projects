import { useState } from 'react';
import { authService } from '../../services/authService';
import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle } from 'lucide-react';

export const Register = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await authService.register(username, email, password);
            navigate('/login');
        } catch (err) {
            setError('Registration failed. Username or email may apply.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[60vh] flex items-center justify-center">
            <div className="bg-fintech-card border border-fintech-border p-8 rounded-xl w-full max-w-md shadow-2xl shadow-black/50">
                <div className="mb-8 text-center">
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-fintech-success to-fintech-primary bg-clip-text text-transparent mb-2">
                        Create Account
                    </h2>
                    <p className="text-fintech-text-muted text-sm">Join the platform to access premium analytics</p>
                </div>

                {error && (
                    <div className="bg-fintech-error/10 border border-fintech-error/20 text-fintech-error p-3 rounded mb-6 text-sm flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        {error}
                    </div>
                )}

                <form onSubmit={handleRegister} className="space-y-5">
                    <div>
                        <label className="block text-fintech-text-secondary text-sm font-medium mb-1.5">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full bg-fintech-bg border border-fintech-border rounded-lg px-4 py-2.5 text-fintech-text-primary focus:outline-none focus:border-fintech-success focus:ring-1 focus:ring-fintech-success transition-colors placeholder:text-fintech-text-muted/50"
                            placeholder="Choose a username"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-fintech-text-secondary text-sm font-medium mb-1.5">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-fintech-bg border border-fintech-border rounded-lg px-4 py-2.5 text-fintech-text-primary focus:outline-none focus:border-fintech-success focus:ring-1 focus:ring-fintech-success transition-colors placeholder:text-fintech-text-muted/50"
                            placeholder="name@example.com"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-fintech-text-secondary text-sm font-medium mb-1.5">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-fintech-bg border border-fintech-border rounded-lg px-4 py-2.5 text-fintech-text-primary focus:outline-none focus:border-fintech-success focus:ring-1 focus:ring-fintech-success transition-colors placeholder:text-fintech-text-muted/50"
                            placeholder="Create a strong password"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-fintech-success hover:bg-emerald-600 text-white font-bold py-2.5 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.2)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)]"
                    >
                        {loading ? <Loader2 className="animate-spin w-4 h-4" /> : 'Create Account'}
                    </button>
                </form>
                <div className="mt-6 text-center">
                    <button onClick={() => navigate('/login')} className="text-fintech-text-muted hover:text-fintech-success text-sm transition-colors">
                        Already have an account? Login
                    </button>
                </div>
            </div>
        </div>
    );
};
