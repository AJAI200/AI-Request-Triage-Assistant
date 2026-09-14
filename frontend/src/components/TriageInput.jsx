import React, { useState, useRef, useEffect } from 'react';
import { Layers, ArrowRight, ShieldCheck, Sparkles, Terminal } from 'lucide-react';

export const MOCK_REQUESTS = [
  {
    id: "01",
    tag: "Req 01",
    label: "Automation",
    text: "Our team has 40 employees entering the same customer details into three systems. Could you show us how this might be automated? We would like to speak next week."
  },
  {
    id: "02",
    tag: "Req 02",
    label: "Portal Outage",
    text: "The client portal has been unavailable since this morning and our staff cannot access active customer records. Please help as soon as possible."
  },
  {
    id: "03",
    tag: "Req 03",
    label: "Duplicate Invoice",
    text: "Invoice NS-1048 appears to include the same implementation charge twice. Can someone review it before payment is processed Friday?"
  },
  {
    id: "04",
    tag: "Req 04",
    label: "Dark Mode",
    text: "Can you add dark mode and change the dashboard font? There is no deadline. I am collecting ideas for a future update."
  },
  {
    id: "05",
    tag: "Req 05",
    label: "Data Exposure",
    text: "We accidentally uploaded a spreadsheet containing customer contact information to the wrong workspace. We need immediate help removing access."
  },
  {
    id: "06",
    tag: "Req 06",
    label: "AI Reporting",
    text: "I saw your company online and am interested in a custom AI reporting system. What would pricing and a typical timeline look like?"
  }
];

export default function TriageInput({
  requestText,
  setRequestText,
  selectedMockIdx,
  setSelectedMockIdx,
  onSubmit,
  loading
}) {
  const [isTyping, setIsTyping] = useState(false);
  const typingTimerRef = useRef(null);

  // Clear timer on unmount
  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearInterval(typingTimerRef.current);
    };
  }, []);

  const handleSelectMock = (index) => {
    if (index === selectedMockIdx) return;
    setSelectedMockIdx(index);

    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
    }

    const fullText = MOCK_REQUESTS[index].text;
    setRequestText("");
    setIsTyping(true);

    let charIdx = 0;
    typingTimerRef.current = setInterval(() => {
      charIdx++;
      if (charIdx <= fullText.length) {
        setRequestText(fullText.slice(0, charIdx));
      } else {
        clearInterval(typingTimerRef.current);
        setIsTyping(false);
      }
    }, 12); // Fast 12ms per char fluid typewriter
  };

  const handleManualInput = (e) => {
    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
    }
    setIsTyping(false);
    setSelectedMockIdx(null);
    setRequestText(e.target.value);
  };

  return (
    <section className="pill-card p-7 space-y-6 bg-white border-2 border-[#FFE0B2] shadow-xl relative overflow-hidden">
      <div>
        <div className="flex items-center justify-between mb-4">
          <label className="block text-xs font-extrabold uppercase tracking-wider text-[#FF5C00] flex items-center gap-2">
            <Layers className="w-4 h-4" />
            Select Mock Request Scenario or Paste Client Email
          </label>
          <span className="text-xs font-extrabold text-[#7A6B63] bg-[#FFF8EE] px-3 py-1 rounded-full border border-[#FFE0B2]">
            6 Presets
          </span>
        </div>
        
        {/* Sleek Polished Mock Scenario Chips */}
        <div className="flex flex-wrap gap-2.5 mb-6">
          {MOCK_REQUESTS.map((req, idx) => {
            const isSelected = selectedMockIdx === idx;
            return (
              <button
                key={req.id}
                type="button"
                onClick={() => handleSelectMock(idx)}
                className={`group relative text-xs font-extrabold px-4 py-2.5 rounded-2xl border-2 transition-all duration-200 active:scale-95 hover:-translate-y-0.5 flex items-center gap-2.5 ${
                  isSelected
                    ? "bg-gradient-to-r from-[#FF5C00] to-[#FF8C42] border-[#FF5C00] text-white shadow-[0_8px_22px_rgba(255,92,0,0.38)]"
                    : "bg-[#FFF8EE] border-[#FFE0B2] text-[#2D1F17] hover:border-[#FF5C00] hover:bg-white hover:shadow-[0_6px_20px_rgba(255,92,0,0.14)]"
                }`}
              >
                <span className={`text-[10px] font-black px-2 py-0.5 rounded-lg uppercase tracking-wider transition-colors ${
                  isSelected 
                    ? "bg-white/20 text-white" 
                    : "bg-[#FFE0B2]/60 text-[#FF5C00] group-hover:bg-[#FF5C00] group-hover:text-white"
                }`}>
                  {req.tag}
                </span>
                <span className="font-bold">{req.label}</span>
                <Sparkles className={`w-3.5 h-3.5 transition-transform duration-300 group-hover:rotate-12 ${
                  isSelected ? "text-white animate-pulse" : "text-[#FF5C00]"
                }`} />
              </button>
            );
          })}
        </div>

        {/* Textarea with Generous Padding & Spacing */}
        <div className="relative group">
          <textarea
            rows="5"
            value={requestText}
            onChange={handleManualInput}
            placeholder="Paste or type an unstructured client request here..."
            className="w-full bg-[#FFF8EE] border-2 border-[#FFE0B2] rounded-3xl p-6 pt-5 pb-10 text-sm font-semibold text-[#2D1F17] leading-relaxed placeholder:text-[#9A8B83] placeholder:font-medium transition-all duration-200 resize-y group-hover:border-[#FF5C00]/60"
          ></textarea>
          
          {/* Typewriter Status & Counter */}
          <div className="absolute bottom-4 right-4 text-xs font-mono text-[#7A6B63] flex items-center gap-2 bg-white px-3.5 py-1.5 rounded-full border border-[#FFE0B2] shadow-sm">
            {isTyping && (
              <span className="text-[#FF5C00] font-bold flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 animate-pulse" />
                <span>Typing</span>
                <span className="w-1.5 h-3 bg-[#FF5C00] inline-block animate-ping rounded-full"></span>
              </span>
            )}
            <span>{requestText.trim().length} / 5000</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2">
        <span className="text-xs font-semibold text-[#7A6B63] hidden sm:inline-flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-[#FF5C00]" />
          <span>Secured Session Authentication</span>
        </span>
        <button
          type="button"
          onClick={onSubmit}
          disabled={!requestText.trim() || loading || isTyping}
          className="pill-btn btn-orange w-full sm:w-auto font-extrabold text-sm px-9 py-3.5 flex items-center justify-center gap-2 shadow-lg disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
        >
          <span>{loading ? "Triaging..." : "Triage Request"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </section>
  );
}
