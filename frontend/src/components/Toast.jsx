import React from 'react';
import { CheckCircle2 } from 'lucide-react';

export default function Toast({ message }) {
  if (!message) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 rounded-full bg-[#2D1F17] text-white border-2 border-[#FF5C00] px-6 py-3.5 shadow-[0_12px_32px_rgba(45,31,23,0.35)] text-xs font-extrabold flex items-center gap-3 transition-all duration-300 animate-in slide-in-from-bottom-4">
      <div className="w-6 h-6 rounded-full bg-[#FF5C00] flex items-center justify-center text-white flex-shrink-0 shadow-sm">
        <CheckCircle2 className="w-4 h-4" />
      </div>
      <span className="text-white text-xs font-extrabold tracking-wide">{message}</span>
    </div>
  );
}
