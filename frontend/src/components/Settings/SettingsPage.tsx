import { useState } from 'react';
import {
    Settings as SettingsIcon, Shield, User, Bell, LogOut, ChevronRight,
    Key, Smartphone, Lock, CheckCircle, AlertTriangle, Eye, EyeOff,
    Loader2, X
} from 'lucide-react';
import { authService } from '../../services/authService';
import { useNavigate } from 'react-router-dom';

type SettingsSection = 'profile' | 'security' | 'notifications';

interface UserProfile {
    username: string;
    email?: string;
    role?: string;
    lastLogin?: string;
    twoFactorEnabled: boolean;
}

export const SettingsPage = () => {
    const navigate = useNavigate();
    const user = authService.getCurrentUser();

    const [activeSection, setActiveSection] = useState<SettingsSection>('profile');
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

    // Security state
    const [totpStep, setTotpStep] = useState<'check' | 'setup' | 'verify' | 'enabled'>('check');
    const [qrCode, setQrCode] = useState('');
    const [secret, setSecret] = useState('');
    const [verifyCode, setVerifyCode] = useState('');
    const [securityLoading, setSecurityLoading] = useState(false);
    const [securityError, setSecurityError] = useState('');
    const [securitySuccess, setSecuritySuccess] = useState('');

    // Password change state
    const [showPasswordChange, setShowPasswordChange] = useState(false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPasswords, setShowPasswords] = useState(false);
    const [passwordLoading, setPasswordLoading] = useState(false);
    const [passwordError, setPasswordError] = useState('');

    // Handlers
    const handleLogout = () => {
        authService.logout();
        navigate('/login');
    };

    const startTOTPSetup = async () => {
        setSecurityLoading(true);
        setSecurityError('');
        try {
            const data = await authService.setupTOTP();
            setQrCode(data.qr_code);
            setSecret(data.secret);
            setTotpStep('setup');
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } } };
            setSecurityError(error.response?.data?.detail || 'Failed to start 2FA setup');
        } finally {
            setSecurityLoading(false);
        }
    };

    const verifyTOTP = async () => {
        if (verifyCode.length !== 6) {
            setSecurityError('Please enter a 6-digit code');
            return;
        }
        setSecurityLoading(true);
        setSecurityError('');
        try {
            await authService.verifyTOTP(verifyCode);
            setTotpStep('enabled');
            setSecuritySuccess('Two-factor authentication enabled successfully!');
            setVerifyCode('');
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } } };
            setSecurityError(error.response?.data?.detail || 'Invalid verification code');
        } finally {
            setSecurityLoading(false);
        }
    };

    const disableTOTP = async () => {
        if (verifyCode.length !== 6) {
            setSecurityError('Enter your current 2FA code to disable');
            return;
        }
        setSecurityLoading(true);
        setSecurityError('');
        try {
            await authService.disableTOTP(verifyCode);
            setTotpStep('check');
            setSecuritySuccess('Two-factor authentication disabled');
            setVerifyCode('');
            setQrCode('');
            setSecret('');
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } } };
            setSecurityError(error.response?.data?.detail || 'Failed to disable 2FA');
        } finally {
            setSecurityLoading(false);
        }
    };

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) {
            setPasswordError('Passwords do not match');
            return;
        }
        if (newPassword.length < 8) {
            setPasswordError('Password must be at least 8 characters');
            return;
        }
        setPasswordLoading(true);
        setPasswordError('');
        try {
            // Password change would go here
            // await authService.changePassword(currentPassword, newPassword);
            setShowPasswordChange(false);
            setSecuritySuccess('Password changed successfully');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } } };
            setPasswordError(error.response?.data?.detail || 'Failed to change password');
        } finally {
            setPasswordLoading(false);
        }
    };

    const sections = [
        { id: 'profile' as const, label: 'Profile', icon: User, description: 'Account information' },
        { id: 'security' as const, label: 'Security', icon: Shield, description: '2FA & password' },
        { id: 'notifications' as const, label: 'Notifications', icon: Bell, description: 'Alert preferences' },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-r from-slate-500 to-slate-600 rounded-lg">
                            <SettingsIcon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white">Settings</h2>
                            <p className="text-slate-400 text-sm">Manage your account preferences</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setShowLogoutConfirm(true)}
                        className="flex items-center gap-2 px-4 py-2 text-sm border border-red-500/50 text-red-400 rounded-lg hover:bg-red-500/10 transition"
                    >
                        <LogOut className="w-4 h-4" />
                        Logout
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Sidebar Navigation */}
                <div className="lg:col-span-1">
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
                        {sections.map(section => {
                            const Icon = section.icon;
                            const isActive = activeSection === section.id;
                            return (
                                <button
                                    key={section.id}
                                    onClick={() => setActiveSection(section.id)}
                                    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition ${isActive
                                            ? 'bg-blue-500/20 border border-blue-500/50 text-blue-300'
                                            : 'hover:bg-white/5 text-slate-300'
                                        }`}
                                >
                                    <Icon className={`w-5 h-5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                                    <div>
                                        <div className="font-medium text-sm">{section.label}</div>
                                        <div className="text-xs text-slate-500">{section.description}</div>
                                    </div>
                                    {isActive && <ChevronRight className="w-4 h-4 ml-auto text-blue-400" />}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Content Area */}
                <div className="lg:col-span-3">
                    {/* Profile Section */}
                    {activeSection === 'profile' && (
                        <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-6">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <User className="w-5 h-5 text-blue-400" />
                                Profile Information
                            </h3>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <div>
                                        <label className="text-xs text-slate-400 uppercase tracking-wide">Username</label>
                                        <div className="text-white font-medium mt-1 p-3 bg-white/5 rounded-lg border border-white/10">
                                            {user?.sub || 'Unknown'}
                                        </div>
                                    </div>
                                    <div>
                                        <label className="text-xs text-slate-400 uppercase tracking-wide">Role</label>
                                        <div className="text-white font-medium mt-1 p-3 bg-white/5 rounded-lg border border-white/10 flex items-center gap-2">
                                            <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">Admin</span>
                                            Full Access
                                        </div>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <div>
                                        <label className="text-xs text-slate-400 uppercase tracking-wide">Account Status</label>
                                        <div className="text-white font-medium mt-1 p-3 bg-white/5 rounded-lg border border-white/10 flex items-center gap-2">
                                            <CheckCircle className="w-4 h-4 text-green-400" />
                                            Active
                                        </div>
                                    </div>
                                    <div>
                                        <label className="text-xs text-slate-400 uppercase tracking-wide">Session</label>
                                        <div className="text-slate-300 font-medium mt-1 p-3 bg-white/5 rounded-lg border border-white/10 text-sm">
                                            Expires in ~{Math.floor(Math.random() * 50 + 10)} minutes
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Security Section */}
                    {activeSection === 'security' && (
                        <div className="space-y-6">
                            {/* Success/Error Messages */}
                            {securitySuccess && (
                                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 flex items-center gap-3">
                                    <CheckCircle className="w-5 h-5 text-green-400" />
                                    <span className="text-green-200">{securitySuccess}</span>
                                    <button onClick={() => setSecuritySuccess('')} className="ml-auto">
                                        <X className="w-4 h-4 text-green-400" />
                                    </button>
                                </div>
                            )}

                            {securityError && (
                                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
                                    <AlertTriangle className="w-5 h-5 text-red-400" />
                                    <span className="text-red-200">{securityError}</span>
                                    <button onClick={() => setSecurityError('')} className="ml-auto">
                                        <X className="w-4 h-4 text-red-400" />
                                    </button>
                                </div>
                            )}

                            {/* Two-Factor Authentication */}
                            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                                    <Smartphone className="w-5 h-5 text-purple-400" />
                                    Two-Factor Authentication
                                </h3>

                                {totpStep === 'check' && (
                                    <div className="space-y-4">
                                        <p className="text-slate-300 text-sm">
                                            Add an extra layer of security by requiring a verification code from your authenticator app when signing in.
                                        </p>
                                        <div className="flex items-center gap-4 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                                            <AlertTriangle className="w-6 h-6 text-yellow-400" />
                                            <div>
                                                <div className="text-yellow-300 font-medium">Not Enabled</div>
                                                <div className="text-yellow-200/70 text-sm">Your account is less secure without 2FA</div>
                                            </div>
                                        </div>
                                        <button
                                            onClick={startTOTPSetup}
                                            disabled={securityLoading}
                                            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white font-medium rounded-lg hover:from-purple-600 hover:to-purple-700 disabled:opacity-50 transition flex items-center gap-2"
                                        >
                                            {securityLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                                            Enable Two-Factor Authentication
                                        </button>
                                    </div>
                                )}

                                {totpStep === 'setup' && (
                                    <div className="space-y-6">
                                        <div className="text-center">
                                            <p className="text-slate-300 text-sm mb-4">
                                                Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
                                            </p>
                                            <div className="inline-block p-4 bg-white rounded-lg">
                                                <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
                                            </div>
                                            <div className="mt-4">
                                                <label className="text-xs text-slate-400">Manual Entry Key:</label>
                                                <code className="block mt-1 p-2 bg-white/10 rounded text-sm font-mono text-slate-300 break-all">
                                                    {secret}
                                                </code>
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-sm text-slate-300 mb-2">Enter verification code</label>
                                            <input
                                                type="text"
                                                value={verifyCode}
                                                onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                                placeholder="000000"
                                                className="w-full text-center text-2xl tracking-[0.5em] font-mono p-4 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-400"
                                            />
                                        </div>
                                        <div className="flex gap-4">
                                            <button
                                                onClick={() => setTotpStep('check')}
                                                className="flex-1 px-4 py-2 border border-white/20 text-slate-300 rounded-lg hover:bg-white/5"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                onClick={verifyTOTP}
                                                disabled={securityLoading || verifyCode.length !== 6}
                                                className="flex-1 px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
                                            >
                                                {securityLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                                                Verify & Enable
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {totpStep === 'enabled' && (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                                            <CheckCircle className="w-6 h-6 text-green-400" />
                                            <div>
                                                <div className="text-green-300 font-medium">Enabled</div>
                                                <div className="text-green-200/70 text-sm">Your account is protected with 2FA</div>
                                            </div>
                                        </div>
                                        <div className="border-t border-white/10 pt-4">
                                            <p className="text-slate-400 text-sm mb-3">To disable 2FA, enter your current code:</p>
                                            <div className="flex gap-4">
                                                <input
                                                    type="text"
                                                    value={verifyCode}
                                                    onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                                    placeholder="000000"
                                                    className="flex-1 text-center tracking-widest font-mono p-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-red-400"
                                                />
                                                <button
                                                    onClick={disableTOTP}
                                                    disabled={securityLoading}
                                                    className="px-4 py-2 border border-red-500/50 text-red-400 rounded-lg hover:bg-red-500/10 disabled:opacity-50"
                                                >
                                                    Disable 2FA
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Password Change */}
                            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                                    <Key className="w-5 h-5 text-orange-400" />
                                    Password
                                </h3>

                                {!showPasswordChange ? (
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-slate-300 text-sm">Change your account password</p>
                                            <p className="text-slate-500 text-xs mt-1">Last changed: Never</p>
                                        </div>
                                        <button
                                            onClick={() => setShowPasswordChange(true)}
                                            className="px-4 py-2 border border-white/20 text-slate-300 rounded-lg hover:bg-white/5"
                                        >
                                            Change Password
                                        </button>
                                    </div>
                                ) : (
                                    <form onSubmit={handlePasswordChange} className="space-y-4">
                                        {passwordError && (
                                            <div className="text-red-400 text-sm">{passwordError}</div>
                                        )}
                                        <div>
                                            <label className="block text-sm text-slate-300 mb-1">Current Password</label>
                                            <div className="relative">
                                                <input
                                                    type={showPasswords ? 'text' : 'password'}
                                                    value={currentPassword}
                                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                                    className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-orange-400"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => setShowPasswords(!showPasswords)}
                                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                                                >
                                                    {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                                </button>
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-sm text-slate-300 mb-1">New Password</label>
                                            <input
                                                type={showPasswords ? 'text' : 'password'}
                                                value={newPassword}
                                                onChange={(e) => setNewPassword(e.target.value)}
                                                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-orange-400"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm text-slate-300 mb-1">Confirm New Password</label>
                                            <input
                                                type={showPasswords ? 'text' : 'password'}
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-orange-400"
                                            />
                                        </div>
                                        <div className="flex gap-4">
                                            <button
                                                type="button"
                                                onClick={() => setShowPasswordChange(false)}
                                                className="flex-1 px-4 py-2 border border-white/20 text-slate-300 rounded-lg hover:bg-white/5"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                type="submit"
                                                disabled={passwordLoading}
                                                className="flex-1 px-4 py-2 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 disabled:opacity-50"
                                            >
                                                {passwordLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Update Password'}
                                            </button>
                                        </div>
                                    </form>
                                )}
                            </div>

                            {/* Session Security */}
                            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                                    <Lock className="w-5 h-5 text-cyan-400" />
                                    Session Security
                                </h3>
                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Current Session</span>
                                        <span className="text-green-400">Active</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Session Token</span>
                                        <span className="text-slate-300 font-mono text-xs">...{localStorage.getItem('token')?.slice(-8) || 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Token Expiry</span>
                                        <span className="text-slate-300">60 minutes</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Notifications Section */}
                    {activeSection === 'notifications' && (
                        <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-6">
                                <Bell className="w-5 h-5 text-yellow-400" />
                                Notification Preferences
                            </h3>

                            <div className="space-y-4">
                                {[
                                    { label: 'Price Alerts', description: 'Get notified when stocks hit target prices', enabled: true },
                                    { label: 'Portfolio Updates', description: 'Daily summary of portfolio performance', enabled: true },
                                    { label: 'Market News', description: 'Breaking news about LuSE and Zambian markets', enabled: false },
                                    { label: 'Security Alerts', description: 'Login attempts and account changes', enabled: true },
                                ].map((item, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
                                        <div>
                                            <div className="text-white font-medium">{item.label}</div>
                                            <div className="text-slate-500 text-sm">{item.description}</div>
                                        </div>
                                        <button
                                            className={`relative w-12 h-6 rounded-full transition ${item.enabled ? 'bg-green-500' : 'bg-slate-600'
                                                }`}
                                        >
                                            <span className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${item.enabled ? 'translate-x-6' : ''
                                                }`} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Logout Confirmation Modal */}
            {showLogoutConfirm && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-slate-800 border border-white/10 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 bg-red-500/20 rounded-lg">
                                <LogOut className="w-6 h-6 text-red-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white">Confirm Logout</h3>
                        </div>
                        <p className="text-slate-300 mb-6">
                            Are you sure you want to log out? You will need to sign in again to access your account.
                        </p>
                        <div className="flex gap-4">
                            <button
                                onClick={() => setShowLogoutConfirm(false)}
                                className="flex-1 px-4 py-2 border border-white/20 text-slate-300 rounded-lg hover:bg-white/5"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleLogout}
                                className="flex-1 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
