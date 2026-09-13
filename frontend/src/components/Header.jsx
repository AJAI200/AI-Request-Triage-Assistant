import React from 'react';
import { Sparkles, KeyRound, LogOut, UserCheck } from 'lucide-react';
import { decodeJwt } from '../utils/jwt';

export default function Header({ jwtToken, onOpenLogin, onLogout }) {
  const claims = jwtToken ? decodeJwt(jwtToken) : null;
  const username = claims?.sub || claims?.username || '';
  const role = claims?.role || 'user';
  const roleDisplay = username ? `${username} (${role})` : role;

  return (
    <header className="sticky top-0 z-40 bg-[#FFF8EE]/90 backdrop-blur-md border-b-2 border-[#FFE0B2]">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-2xl bg-[#FF5C00] text-white flex items-center justify-center shadow-[0_8px_20px_rgba(255,92,0,0.3)]">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-[#2D1F17] tracking-tight">
              AI Request Triage Assistant
            </h1>
            <p className="text-xs text-[#7A6B63]">Node Solutions • Stage Two Challenge</p>
          </div>
        </div>

        {/* Auth Badge & Buttons */}
        <div className="flex items-center space-x-3">
          {jwtToken ? (
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-2 text-xs font-extrabold text-emerald-800 bg-emerald-100 border-2 border-emerald-300 px-4 py-2 rounded-full shadow-sm">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="flex items-center gap-1">
                  <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                  JWT Active ({roleDisplay})
                </span>
              </div>
              <button
                type="button"
                onClick={onLogout}
                className="text-xs font-extrabold text-[#2D1F17] bg-white hover:bg-[#FFF4E5] border-2 border-[#FFE0B2] px-4 py-2 rounded-full transition-all duration-150 flex items-center gap-1.5 active:scale-95 shadow-sm hover:border-[#FF5C00]"
              >
                <LogOut className="w-3.5 h-3.5 text-[#FF5C00]" />
                <span>Sign Out</span>
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={onOpenLogin}
              className="pill-btn btn-orange text-xs font-extrabold px-5 py-2.5 flex items-center gap-2 shadow-[0_8px_20px_rgba(255,92,0,0.25)] active:scale-95"
            >
              <KeyRound className="w-4 h-4" />
              <span>Sign In (JWT Auth)</span>
            </button>
          )}
        </div>

      </div>
    </header>
  );
}

