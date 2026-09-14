import React, { useState } from 'react';
import { KeyRound, X, AlertCircle, LogIn, UserPlus, CheckCircle2, Circle, Eye, EyeOff } from 'lucide-react';
import { login, register } from '../services/api';

const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

export default function JwtModal({ isOpen, onClose, onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  // Validation checks for registration
  const passLength = password.length >= 8;
  const passUpper = /[A-Z]/.test(password);
  const passLower = /[a-z]/.test(password);
  const passNumber = /[0-9]/.test(password);
  const passSpecialCount = (password.match(/[#$%&*()!@]/g) || []).length;
  const passSpecial = passSpecialCount >= 3;
  const isPasswordValid = passLength && passUpper && passLower && passNumber && passSpecial;

  const isEmailFormat = username.includes('@');
  const isEmailValid = isEmailFormat ? EMAIL_REGEX.test(username) : username.trim().length >= 3;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (activeTab === 'register') {
      if (isEmailFormat && !EMAIL_REGEX.test(username)) {
        setError('Please enter a valid email address (e.g. user@gmail.com).');
        return;
      }
      if (!isPasswordValid) {
        setError('Password does not meet the complexity requirements.');
        return;
      }
    }

    setLoading(true);

    try {
      const authFn = activeTab === 'login' ? login : register;
      const res = await authFn(username.trim(), password);

      if (res.ok) {
        const data = await res.json();
        onLoginSuccess(data.access_token, activeTab === 'register' ? 'Account created successfully!' : 'Signed in successfully!');
        onClose();
        setLoading(false);
        return;
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || `${activeTab === 'login' ? 'Authentication' : 'Registration'} failed (Status ${res.status})`);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="pill-card max-w-md w-full p-7 space-y-5 bg-white border-2 border-[#FFE0B2] shadow-2xl relative">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b-2 border-[#FFE0B2] pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-[#FF5C00]/10 border border-[#FF5C00]/30 flex items-center justify-center text-[#FF5C00]">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-[#2D1F17]">User Authentication</h2>
              <p className="text-xs text-[#7A6B63]">Sign in or create an account to access the platform</p>
            </div>
          </div>
          <button onClick={onClose} className="text-[#7A6B63] hover:text-[#2D1F17]">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="grid grid-cols-2 p-1 bg-[#FFF8EE] border border-[#FFE0B2] rounded-2xl">
          <button
            type="button"
            onClick={() => { setActiveTab('login'); setError(null); }}
            className={`py-2 text-xs font-extrabold rounded-xl transition-all duration-150 flex items-center justify-center gap-1.5 ${
              activeTab === 'login'
                ? "bg-white text-[#FF5C00] shadow-sm border border-[#FFE0B2]"
                : "text-[#7A6B63] hover:text-[#2D1F17]"
            }`}
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('register'); setError(null); }}
            className={`py-2 text-xs font-extrabold rounded-xl transition-all duration-150 flex items-center justify-center gap-1.5 ${
              activeTab === 'register'
                ? "bg-white text-[#FF5C00] shadow-sm border border-[#FFE0B2]"
                : "text-[#7A6B63] hover:text-[#2D1F17]"
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Create Account</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-50 border-2 border-rose-200 text-rose-700 px-4 py-3 rounded-xl text-xs font-semibold flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#7A6B63] mb-1.5">
              Username or Email
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="e.g. user@gmail.com"
              className="w-full bg-[#FFF8EE] border-2 border-[#FFE0B2] rounded-xl px-4 py-2.5 text-sm font-semibold text-[#2D1F17] placeholder-zinc-400"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#7A6B63] mb-1.5">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter your password"
                className="w-full bg-[#FFF8EE] border-2 border-[#FFE0B2] rounded-xl px-4 py-2.5 pr-11 text-sm font-semibold text-[#2D1F17] placeholder-zinc-400"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#7A6B63] hover:text-[#FF5C00] p-1 transition-colors"
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>


          {/* Real-time Password Requirements Checklist (Register Mode) */}
          {activeTab === 'register' && (
            <div className="bg-[#FFF8EE] border border-[#FFE0B2] p-3.5 rounded-xl space-y-1.5 text-xs">
              <span className="block font-bold text-[#7A6B63] mb-1">Password Requirements:</span>
              <div className={`flex items-center gap-2 ${passLength ? "text-emerald-700 font-semibold" : "text-zinc-500"}`}>
                {passLength ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" /> : <Circle className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />}
                <span>At least 8 characters</span>
              </div>
              <div className={`flex items-center gap-2 ${passUpper && passLower ? "text-emerald-700 font-semibold" : "text-zinc-500"}`}>
                {passUpper && passLower ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" /> : <Circle className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />}
                <span>Both uppercase (A-Z) & lowercase (a-z) letters</span>
              </div>
              <div className={`flex items-center gap-2 ${passNumber ? "text-emerald-700 font-semibold" : "text-zinc-500"}`}>
                {passNumber ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" /> : <Circle className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />}
                <span>At least 1 number (0-9)</span>
              </div>
              <div className={`flex items-center gap-2 ${passSpecial ? "text-emerald-700 font-semibold" : "text-zinc-500"}`}>
                {passSpecial ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" /> : <Circle className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />}
                <span>At least 3 special characters ({passSpecialCount}/3: #$%&*()!@)</span>
              </div>
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading || (activeTab === 'register' && (!isPasswordValid || !isEmailValid))}
              className="pill-btn btn-orange w-full py-3 text-sm font-extrabold flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span>Processing...</span>
              ) : activeTab === 'login' ? (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  <span>Create Account</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}



