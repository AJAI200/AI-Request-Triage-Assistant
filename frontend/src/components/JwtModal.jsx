import React, { useState } from 'react';
import { KeyRound, X, AlertCircle, Sparkles, LogIn } from 'lucide-react';
import { login } from '../services/api';

export default function JwtModal({ isOpen, onClose, onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await login(username, password);

      if (res.ok) {
        const data = await res.json();
        onLoginSuccess(data.access_token);
        onClose();
        setLoading(false);
        return;
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || `Authentication failed (Status ${res.status})`);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = () => {
    setUsername('admin');
    setPassword('password123');
  };

  const isDev = import.meta.env.DEV;

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
              <h2 className="text-base font-extrabold text-[#2D1F17]">JWT User Authentication</h2>
              <p className="text-xs text-[#7A6B63]">Sign in to generate a Bearer Token</p>
            </div>
          </div>
          <button onClick={onClose} className="text-[#7A6B63] hover:text-[#2D1F17]">
            <X className="w-5 h-5" />
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
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Enter username"
              className="w-full bg-[#FFF8EE] border-2 border-[#FFE0B2] rounded-xl px-4 py-2.5 text-sm font-semibold text-[#2D1F17] placeholder-zinc-400"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#7A6B63] mb-1.5">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter password"
              className="w-full bg-[#FFF8EE] border-2 border-[#FFE0B2] rounded-xl px-4 py-2.5 text-sm font-semibold text-[#2D1F17] placeholder-zinc-400"
            />
          </div>

          {isDev && (
            <div className="flex items-center justify-between text-xs text-[#7A6B63] pt-1">
              <button
                type="button"
                onClick={fillDemoCredentials}
                className="text-[#FF5C00] hover:underline flex items-center gap-1 font-bold"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Use Demo Credentials</span>
              </button>
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="pill-btn btn-orange w-full py-3 text-sm font-extrabold flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
            >
              {loading ? (
                <span>Signing In...</span>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In & Generate JWT</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

