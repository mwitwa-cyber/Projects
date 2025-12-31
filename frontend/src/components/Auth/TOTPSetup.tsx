import { useState } from 'react';
import { authService } from '../../services/authService';
import { Shield, CheckCircle } from 'lucide-react';

export const TOTPSetup = () => {
    const [step, setStep] = useState<'init' | 'scan' | 'verified'>('init');
    const [qrCode, setQrCode] = useState<string>('');
    const [secret, setSecret] = useState<string>('');
    const [code, setCode] = useState('');
    const [error, setError] = useState<string | null>(null);

    const startSetup = async () => {
        try {
            setError(null);
            const data = await authService.setupTOTP();
            setQrCode(data.qr_code);
            setSecret(data.secret);
            setStep('scan');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to start setup');
        }
    };

    const verifyCode = async () => {
        try {
            setError(null);
            await authService.verifyTOTP(code);
            setStep('verified');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Invalid code');
        }
    };

    const disable2FA = async () => {
        try {
            // Usually requires code, but if we are verified we might need re-auth?
            // For now, assume disable needs a code too.
            if (!code) {
                setError("Please enter a code to confirm disable");
                return;
            }
            await authService.disableTOTP(code);
            setStep('init');
            setQrCode('');
            setCode('');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to disable 2FA');
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 max-w-md mx-auto">
            <div className="flex items-center gap-3 mb-4">
                <Shield className="w-6 h-6 text-blue-600" />
                <h2 className="text-xl font-bold text-gray-900">Two-Factor Authentication</h2>
            </div>

            {step === 'init' && (
                <div className="space-y-4">
                    <p className="text-gray-600 text-sm">
                        Secure your account by enabling 2FA. You will need an authenticator app like Google Authenticator or Authy.
                    </p>
                    <button
                        onClick={startSetup}
                        className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
                    >
                        Enable 2FA
                    </button>
                    {error && <p className="text-red-500 text-sm">{error}</p>}
                </div>
            )}

            {step === 'scan' && (
                <div className="space-y-4 animate-fade-in">
                    <div className="text-center">
                        <img src={qrCode} alt="TOTP QR Code" className="mx-auto border p-2 rounded-lg" />
                        <p className="text-xs text-gray-500 mt-2 font-mono break-all">{secret}</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Enter Verification Code</label>
                        <input
                            type="text"
                            className="w-full text-center tracking-widest text-lg p-2 border rounded-md"
                            placeholder="000000"
                            maxLength={6}
                            value={code}
                            onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                        />
                    </div>

                    <button
                        onClick={verifyCode}
                        className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 flex items-center justify-center gap-2"
                    >
                        Verify & Enable
                    </button>

                    <button onClick={() => setStep('init')} className="text-sm text-gray-500 w-full text-center hover:underline">
                        Cancel
                    </button>

                    {error && <p className="text-red-500 text-sm text-center">{error}</p>}
                </div>
            )}

            {step === 'verified' && (
                <div className="text-center space-y-4 animate-fade-in">
                    <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
                    <h3 className="text-lg font-semibold text-green-700">2FA Enabled</h3>
                    <p className="text-sm text-gray-600">Your account is now secured with two-factor authentication.</p>

                    <div className="border-t pt-4 mt-4">
                        <p className="text-xs text-gray-400 mb-2">Need to disable it?</p>
                        <input
                            type="text"
                            className="w-full text-center tracking-widest text-lg p-2 border rounded-md mb-2"
                            placeholder="Enter Code to Disable"
                            maxLength={6}
                            value={code}
                            onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                        />
                        <button
                            onClick={disable2FA}
                            className="text-red-600 text-sm hover:underline"
                        >
                            Disable 2FA
                        </button>
                        {error && <p className="text-red-500 text-sm">{error}</p>}
                    </div>
                </div>
            )}
        </div>
    );
};
