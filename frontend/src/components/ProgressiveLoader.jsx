import React from 'react';
import { Loader2 } from 'lucide-react';

export default function ProgressiveLoader({ stageText, progressPct, longWait }) {
  return (
    <div className="pill-card p-6 space-y-4 border-2 border-[#FF5C00]/30 bg-white shadow-xl animate-in fade-in duration-200">
      <div className="flex items-center space-x-3">
        <Loader2 className="w-5 h-5 text-[#FF5C00] animate-spin flex-shrink-0" />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <span className="text-sm font-extrabold text-[#FF5C00] animate-pulse">
              {stageText}
            </span>
            <span className="text-xs font-mono font-bold text-[#FF5C00]">{progressPct}%</span>
          </div>
        </div>
      </div>

      <div className="w-full bg-[#FFF4E5] rounded-full h-2 overflow-hidden border border-[#FFE0B2]">
        <div
          className="h-full bg-gradient-to-r from-[#FF5C00] via-[#FF7A00] to-[#FFB74D] transition-all duration-300 rounded-full"
          style={{ width: `${progressPct}%` }}
        ></div>
      </div>
      <p className="text-xs text-[#7A6B63] italic">
        {longWait
          ? "Still working — the AI model is taking a bit longer than usual..."
          : "Evaluating sentiment, urgency metrics & departmental assignment logic..."}
      </p>
    </div>
  );
}

