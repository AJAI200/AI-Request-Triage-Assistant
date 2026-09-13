import React, { useState } from 'react';
import { CheckCircle2, FileText, Tag, Zap, UserCheck, MailCheck, Copy, Check, HelpCircle, Users, Sparkles } from 'lucide-react';

export default function TriageResult({ result, onCopyToast }) {
  const [copied, setCopied] = useState(false);

  if (!result) return null;

  const handleCopy = () => {
    if (!result.draft_response) return;
    navigator.clipboard.writeText(result.draft_response).then(() => {
      setCopied(true);
      onCopyToast("Draft response email copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const priority = (result.priority || "Medium").toUpperCase();
  let priorityStyle = {
    badge: "bg-amber-500 text-white border-amber-400 shadow-[0_4px_16px_rgba(245,158,11,0.35)]",
    cardBorder: "border-amber-200/80 bg-gradient-to-br from-white via-amber-50/20 to-white",
    label: "text-amber-700"
  };

  if (priority === "URGENT" || priority === "HIGH") {
    priorityStyle = {
      badge: "bg-gradient-to-r from-rose-500 to-red-600 text-white border-rose-400 shadow-[0_4px_18px_rgba(244,63,94,0.4)] animate-pulse",
      cardBorder: "border-rose-200 bg-gradient-to-br from-white via-rose-50/30 to-white",
      label: "text-rose-700"
    };
  } else if (priority === "LOW") {
    priorityStyle = {
      badge: "bg-emerald-500 text-white border-emerald-400 shadow-[0_4px_14px_rgba(16,185,129,0.3)]",
      cardBorder: "border-emerald-200 bg-gradient-to-br from-white via-emerald-50/20 to-white",
      label: "text-emerald-700"
    };
  }

  // Department icon colors
  const departmentColors = {
    "Engineering": "from-blue-500 to-indigo-600 shadow-blue-500/30",
    "Billing & Finance": "from-amber-500 to-orange-500 shadow-amber-500/30",
    "Client Success": "from-emerald-500 to-teal-600 shadow-emerald-500/30",
    "IT Support": "from-purple-500 to-violet-600 shadow-purple-500/30",
    "Product Management": "from-pink-500 to-rose-600 shadow-pink-500/30"
  };
  const deptGradient = departmentColors[result.owner] || "from-[#FF5C00] to-[#FF8C42] shadow-[#FF5C00]/30";

  return (
    <section id="results-section" className="space-y-6 animate-in fade-in duration-300">
      {/* Header Live Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-[#FFE0B2] pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-gradient-to-r from-[#FF5C00] to-[#FF8C42] flex items-center justify-center shadow-md">
            <CheckCircle2 className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-black text-[#2D1F17] uppercase tracking-wider flex items-center gap-2">
              <span>Triage Classification Output</span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                <span>AI Processed</span>
              </span>
            </h2>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          {result.process_time_ms && (
            <span className="text-xs font-mono font-extrabold text-[#FF5C00] bg-[#FFF8EE] border-2 border-[#FFE0B2] px-3.5 py-1.5 rounded-full shadow-sm flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 fill-[#FF5C00] text-[#FF5C00] animate-bounce" />
              <span>{(result.process_time_ms / 1000).toFixed(2)}s</span>
              <span className="text-[10px] text-[#7A6B63] font-sans">({result.process_time_ms} ms)</span>
            </span>
          )}
          <span className="text-xs font-mono font-black text-[#2D1F17] bg-white border-2 border-[#FFE0B2] px-3.5 py-1.5 rounded-full shadow-sm">
            Req #{result.id}
          </span>
        </div>
      </div>

      {result.status === "classified" ? (
        <div className="space-y-6">
          {/* Executive Summary Card with Glass Glow */}
          <div className="pill-card p-7 bg-white/95 backdrop-blur-md border-2 border-[#FFE0B2] space-y-3 shadow-xl relative overflow-hidden group hover:border-[#FF5C00]/50 transition-all duration-300">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-black uppercase tracking-wider text-[#FF5C00] flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <span>Executive Summary</span>
              </h3>
              <Sparkles className="w-4 h-4 text-[#FF5C00] opacity-60 group-hover:rotate-12 transition-transform duration-300" />
            </div>
            <p className="text-[#2D1F17] text-base leading-relaxed font-bold tracking-tight">
              {result.summary || "No summary generated."}
            </p>
          </div>

          {/* Badges Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Category */}
            <div className="pill-card p-6 bg-white/95 backdrop-blur-md border-2 border-[#FFE0B2] flex flex-col justify-between shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#7A6B63] flex items-center gap-1.5 mb-3">
                <Tag className="w-4 h-4 text-[#FF5C00]" />
                <span>Category</span>
              </span>
              <div>
                <span className="inline-flex items-center gap-1.5 px-4 py-2 rounded-2xl text-xs font-black bg-gradient-to-r from-[#FF5C00] to-[#FF8C42] text-white shadow-[0_6px_18px_rgba(255,92,0,0.32)] border border-[#FF5C00]">
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                  <span>{result.category || "Other"}</span>
                </span>
              </div>
            </div>

            {/* Priority & Reason */}
            <div className={`pill-card p-6 bg-white/95 backdrop-blur-md border-2 flex flex-col justify-between shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5 ${priorityStyle.cardBorder}`}>
              <span className={`text-xs font-extrabold uppercase tracking-wider flex items-center gap-1.5 mb-2 ${priorityStyle.label}`}>
                <Zap className="w-4 h-4 fill-current" />
                <span>Priority & Urgency</span>
              </span>
              <div className="space-y-2.5">
                <div>
                  <span className={`inline-flex items-center px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-wider border ${priorityStyle.badge}`}>
                    {result.priority || "Medium"}
                  </span>
                </div>
                <p className="text-xs text-[#52443C] font-semibold italic leading-relaxed bg-white/70 p-2.5 rounded-xl border border-[#FFE0B2]/60">
                  "{result.priority_reason || "Normal request SLA"}"
                </p>
              </div>
            </div>

            {/* Assigned Department */}
            <div className="pill-card p-6 bg-white/95 backdrop-blur-md border-2 border-[#FFE0B2] flex flex-col justify-between shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#7A6B63] flex items-center gap-1.5 mb-3">
                <UserCheck className="w-4 h-4 text-blue-500" />
                <span>Assigned Department</span>
              </span>
              <div className="flex items-center gap-3.5 bg-[#FFF8EE] p-3 rounded-2xl border border-[#FFE0B2]">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${deptGradient} shadow-md flex items-center justify-center text-white flex-shrink-0 font-black text-sm`}>
                  <Users className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-xs font-bold text-[#7A6B63] block">Owner Team</span>
                  <span className="text-sm font-black text-[#2D1F17]">{result.owner || "Client Success"}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Draft Email Card */}
          <div className="pill-card p-7 bg-white/95 backdrop-blur-md border-2 border-[#FFE0B2] space-y-4 shadow-xl relative overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#FFE0B2] pb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#FF5C00]/10 border border-[#FF5C00]/30 flex items-center justify-center text-[#FF5C00]">
                  <MailCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-black uppercase tracking-wider text-[#2D1F17]">
                    Suggested Customer First-Contact Draft
                  </h3>
                  <span className="text-[11px] font-semibold text-[#7A6B63]">
                    Ready to review, edit, and send to client
                  </span>
                </div>
              </div>

              <button
                onClick={handleCopy}
                className={`pill-btn inline-flex items-center gap-2 text-xs font-extrabold px-5 py-2.5 rounded-full transition-all duration-200 active:scale-95 shadow-md ${
                  copied
                    ? "bg-emerald-600 text-white shadow-emerald-600/30"
                    : "bg-gradient-to-r from-[#FF5C00] to-[#FF8C42] text-white hover:shadow-lg hover:scale-[1.02]"
                }`}
              >
                {copied ? <Check className="w-4 h-4 stroke-[3]" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? "Copied to Clipboard!" : "Copy Draft Response"}</span>
              </button>
            </div>

            {/* Email Body Text */}
            <div className="bg-[#FFF8EE] border-2 border-[#FFE0B2] rounded-3xl p-6 font-sans text-sm font-semibold text-[#2D1F17] leading-relaxed whitespace-pre-wrap selection:bg-[#FF5C00] selection:text-white shadow-inner">
              {result.draft_response || "No draft response generated."}
            </div>
          </div>
        </div>
      ) : (
        <div className="pill-card p-7 bg-amber-50 border-2 border-amber-200 text-amber-900 space-y-3 shadow-lg">
          <div className="flex items-center gap-2.5 font-black text-base text-amber-900">
            <HelpCircle className="w-6 h-6 text-amber-600" />
            <span>Flagged for Manual Review</span>
          </div>
          <p className="text-sm font-semibold leading-relaxed text-amber-800">
            {result.message || "Could not automatically classify this request. Please review manually."}
          </p>
        </div>
      )}
    </section>
  );
}
