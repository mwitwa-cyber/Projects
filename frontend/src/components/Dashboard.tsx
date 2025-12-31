import { useState, useEffect } from 'react';
import { Activity, Zap, BarChart3, AlertCircle, Loader2, Shield } from 'lucide-react';
import { MarketPulse } from './MarketPulse';
import { BondPricer } from './BondPricer';
import { PortfolioOptimizer } from './PortfolioOptimizer';
import { RiskAnalyzer } from './RiskAnalyzer';
import { TOTPSetup } from './Auth/TOTPSetup';
import { healthCheck } from '../services/api';
import { authService } from '../services/authService';
import { useNavigate } from 'react-router-dom';

type TabType = 'market' | 'bond' | 'portfolio' | 'risk' | 'profile';

export function Dashboard() {
    const [activeTab, setActiveTab] = useState<TabType>('market');
    const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
    const navigate = useNavigate();
    const user = authService.getCurrentUser();

    useEffect(() => {
        const checkBackend = async () => {
            try {
                await healthCheck();
                setBackendStatus('online');
            } catch {
                setBackendStatus('offline');
            }
        };

        checkBackend();
        // Check every 30 seconds
        const interval = setInterval(checkBackend, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleLogout = () => {
        authService.logout();
        navigate('/login');
    };

    const tabs = [
        { id: 'market' as const, label: 'Market Pulse', icon: Activity },
        { id: 'bond' as const, label: 'Bond Pricing', icon: Zap },
        { id: 'portfolio' as const, label: 'Portfolio', icon: BarChart3 },
        { id: 'risk' as const, label: 'Risk Analysis', icon: AlertCircle },
        { id: 'profile' as const, label: 'Security', icon: Shield },
    ];

    if (backendStatus === 'checking') {
        return (
            <div className="min-h-screen bg-fintech-bg flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-10 h-10 animate-spin text-fintech-primary mx-auto mb-4" />
                    <p className="text-fintech-text-secondary">Connecting to backend...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-fintech-bg text-fintech-text-primary">
            {/* Header */}
            <header className="border-b border-fintech-border bg-fintech-card/80 backdrop-blur-md sticky top-0 z-50 shadow-lg shadow-black/20">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-fintech-primary to-fintech-success bg-clip-text text-transparent">
                                LuSE Quant Platform
                            </h1>
                            <p className="text-fintech-text-muted text-sm mt-1">Actuarial Finance & Portfolio Optimization</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border ${backendStatus === 'online'
                                ? 'bg-fintech-success/10 border-fintech-success/20 text-fintech-success'
                                : 'bg-fintech-error/10 border-fintech-error/20 text-fintech-error'
                                }`}>
                                <div className={`w-2 h-2 rounded-full ${backendStatus === 'online' ? 'bg-fintech-success' : 'bg-fintech-error'} animate-pulse`} />
                                {backendStatus === 'online' ? 'System Online' : 'System Offline'}
                            </div>
                            <button
                                onClick={handleLogout}
                                className="px-3 py-2 rounded-lg bg-fintech-card border border-fintech-border text-fintech-text-muted hover:text-fintech-error hover:border-fintech-error/50 text-sm font-medium transition-all"
                            >
                                Logout ({user?.sub || 'User'})
                            </button>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex gap-2 overflow-x-auto pb-1">
                        {tabs.map(tab => {
                            const Icon = tab.icon;
                            const isActive = activeTab === tab.id;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 whitespace-nowrap border ${isActive
                                        ? 'bg-fintech-primary/10 border-fintech-primary text-fintech-primary shadow-[0_0_15px_rgba(56,189,248,0.15)]'
                                        : 'bg-transparent border-transparent text-fintech-text-muted hover:bg-fintech-hover hover:text-fintech-text-primary'
                                        }`}
                                >
                                    <Icon className={`w-4 h-4 ${isActive ? 'text-fintech-primary' : ''}`} />
                                    {tab.label}
                                </button>
                            );
                        })}
                    </nav>
                </div>
            </header>

            {/* Content */}
            <main className="max-w-7xl mx-auto px-6 py-8">
                {backendStatus === 'offline' && (
                    <div className="mb-6 bg-fintech-error/5 border border-fintech-error/20 rounded-lg p-4 flex gap-3">
                        <AlertCircle className="w-5 h-5 text-fintech-error flex-shrink-0 mt-0.5" />
                        <div className="text-fintech-text-secondary text-sm">
                            Backend is offline. Please ensure Docker containers are running: <code className="bg-black/30 px-2 py-1 rounded text-white font-mono">docker-compose up -d backend</code>
                        </div>
                    </div>
                )}

                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {activeTab === 'market' && <MarketPulse />}
                    {activeTab === 'bond' && <BondPricer />}
                    {activeTab === 'portfolio' && <PortfolioOptimizer />}
                    {activeTab === 'risk' && <RiskAnalyzer />}
                    {activeTab === 'profile' && <TOTPSetup />}
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-fintech-border bg-fintech-card/30 mt-12 py-8">
                <div className="max-w-7xl mx-auto px-6 text-center">
                    <p className="text-fintech-text-muted text-sm">LuSE Quant Platform © 2025</p>
                    <div className="flex justify-center gap-4 mt-2 text-xs text-fintech-text-muted opacity-60">
                        <span>Production Build v0.1.0</span>
                        <span>•</span>
                        <span>Secure Connection</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}
