import { useState, useEffect } from 'react';
import { Activity, Zap, BarChart3, AlertCircle, Loader2 } from 'lucide-react';
import { MarketPulse } from './components/MarketPulse';
import { BondPricer } from './components/BondPricer';
import { PortfolioOptimizer } from './components/PortfolioOptimizer';
import { RiskAnalyzer } from './components/RiskAnalyzer';
import { healthCheck } from './services/api';

type TabType = 'market' | 'bond' | 'portfolio' | 'risk';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('market');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

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

  const tabs = [
    { id: 'market' as const, label: 'Market Pulse', icon: Activity },
    { id: 'bond' as const, label: 'Bond Pricing', icon: Zap },
    { id: 'portfolio' as const, label: 'Portfolio', icon: BarChart3 },
    { id: 'risk' as const, label: 'Risk Analysis', icon: AlertCircle },
  ];

  if (backendStatus === 'checking') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-blue-400 mx-auto mb-4" />
          <p className="text-slate-300">Connecting to backend...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                LuSE Quant Platform
              </h1>
              <p className="text-slate-400 text-sm mt-1">Actuarial Finance & Portfolio Optimization</p>
            </div>
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${backendStatus === 'online'
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : 'bg-red-500/20 text-red-300'
                }`}>
                <div className={`w-2 h-2 rounded-full ${backendStatus === 'online' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`} />
                {backendStatus === 'online' ? 'Backend Online' : 'Backend Offline'}
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex gap-2 overflow-x-auto">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition whitespace-nowrap ${activeTab === tab.id
                      ? 'bg-blue-500/30 border border-blue-400 text-blue-300'
                      : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
                    }`}
                >
                  <Icon className="w-4 h-4" />
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
          <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-red-200 text-sm">
              Backend is offline. Please ensure Docker containers are running: <code className="bg-red-900/30 px-2 py-1 rounded">docker-compose up -d backend</code>
            </div>
          </div>
        )}

        {activeTab === 'market' && <MarketPulse />}
        {activeTab === 'bond' && <BondPricer />}
        {activeTab === 'portfolio' && <PortfolioOptimizer />}
        {activeTab === 'risk' && <RiskAnalyzer />}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-slate-400 text-sm">
          <p>LuSE Quant Platform © 2025 | Production-Grade Actuarial Infrastructure</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
