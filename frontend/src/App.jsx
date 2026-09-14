import React, { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import Header from './components/Header';
import JwtModal from './components/JwtModal';
import TriageInput from './components/TriageInput';
import ProgressiveLoader from './components/ProgressiveLoader';
import TriageResult from './components/TriageResult';
import Toast from './components/Toast';
import WaterRippleCanvas from './components/WaterRippleCanvas';
import CustomCursor from './components/CustomCursor';
import { useCanvasSize } from './hooks/useCanvasSize';
import { useAuth } from './context/AuthContext';
import { submitTriage } from './services/api';
import { AlertCircle, X } from 'lucide-react';

const LOADING_STAGES = [
  { text: "⚡ Reading customer request text & parsing sentiment...", pct: 20 },
  { text: "🧠 Running Gemini AI categorization & intent models...", pct: 45 },
  { text: "🎯 Evaluating priority urgency & assigning owner team...", pct: 70 },
  { text: "✍️ Drafting tailored response & setting SLA metrics...", pct: 88 },
  { text: "✨ Finalizing triage response package...", pct: 96 }
];

const SHARD_COLORS = [
  { stroke: 'rgba(255, 92, 0, 0.4)', fill: 'rgba(255, 92, 0, 0.12)' },    // Orange
  { stroke: 'rgba(132, 204, 22, 0.4)', fill: 'rgba(132, 204, 22, 0.12)' }, // Lime Green
  { stroke: 'rgba(236, 72, 153, 0.4)', fill: 'rgba(236, 72, 153, 0.12)' }, // Magenta Pink
  { stroke: 'rgba(245, 158, 11, 0.4)', fill: 'rgba(245, 158, 11, 0.12)' }, // Amber Yellow
  { stroke: 'rgba(139, 92, 246, 0.4)', fill: 'rgba(139, 92, 246, 0.12)' }  // Soft Purple
];

export default function App() {
  const { jwtToken, isModalOpen, setIsModalOpen, loginToken, logout } = useAuth();
  const [requestText, setRequestText] = useState("");
  const [selectedMockIdx, setSelectedMockIdx] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [longWait, setLongWait] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [triageResult, setTriageResult] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  const mainRef = useRef(null);
  const canvasRef = useRef(null);
  const abortRef = useRef(null);

  useCanvasSize(canvasRef);

  // Clean up ongoing fetch requests on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // GSAP Entrance Animations
  useGSAP(() => {
    gsap.from(".gsap-header", {
      y: -25,
      opacity: 0,
      duration: 0.6,
      ease: "power3.out"
    });
    gsap.from(".gsap-input-section", {
      y: 30,
      opacity: 0,
      duration: 0.8,
      delay: 0.2,
      ease: "power3.out"
    });
  }, { scope: mainRef });

  // Broken Glowing Glass Particle Canvas Animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    let width = canvas.width;
    let height = canvas.height;

    const particles = [];
    const count = 35;

    for (let i = 0; i < count; i++) {
      const colorScheme = SHARD_COLORS[Math.floor(Math.random() * SHARD_COLORS.length)];
      particles.push({
        x: Math.random() * (width || window.innerWidth),
        y: Math.random() * (height || window.innerHeight),
        size: Math.random() * 6 + 3,
        sides: Math.floor(Math.random() * 3) + 3,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        rot: Math.random() * Math.PI * 2,
        vRot: (Math.random() - 0.5) * 0.015,
        color: colorScheme
      });
    }

    function drawPolygon(ctx, x, y, radius, sides, angle) {
      ctx.beginPath();
      for (let i = 0; i < sides; i++) {
        const a = angle + (i * 2 * Math.PI / sides);
        const px = x + radius * Math.cos(a);
        const py = y + radius * Math.sin(a);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
    }

    let animId;
    function animate() {
      const w = canvas.width || window.innerWidth;
      const h = canvas.height || window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.rot += p.vRot;

        if (p.x < -20) p.x = w + 20;
        if (p.x > w + 20) p.x = -20;
        if (p.y < -20) p.y = h + 20;
        if (p.y > h + 20) p.y = -20;

        ctx.save();
        ctx.strokeStyle = p.color.stroke;
        ctx.fillStyle = p.color.fill;
        ctx.lineWidth = 1.5;
        ctx.shadowBlur = 10;
        ctx.shadowColor = p.color.stroke;

        drawPolygon(ctx, p.x, p.y, p.size, p.sides, p.rot);
        ctx.stroke();
        ctx.fill();
        ctx.restore();
      });

      animId = requestAnimationFrame(animate);
    }

    animate();

    const handleVisibility = () => {
      if (document.hidden) {
        cancelAnimationFrame(animId);
      } else {
        animate();
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibility);
      cancelAnimationFrame(animId);
    };
  }, []);

  const handleLoginSuccess = (token, customMsg) => {
    loginToken(token);
    showToast(customMsg || "Signed in successfully!");
  };

  const handleLogout = () => {
    logout();
    showToast("Signed out. Session cleared.");
  };

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 2800);
  };

  // Smooth Auto-scroll to results whenever triageResult is updated
  useEffect(() => {
    if (triageResult) {
      const timer = setTimeout(() => {
        const resultsEl = document.getElementById("results-section");
        if (resultsEl) {
          resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
          gsap.fromTo(resultsEl, 
            { y: 30, opacity: 0 },
            { y: 0, opacity: 1, duration: 0.7, ease: "power3.out" }
          );
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [triageResult]);

  const handleSubmitTriage = async () => {
    if (!requestText.trim()) return;

    if (!jwtToken) {
      setIsModalOpen(true);
      showToast("Please sign in or create an account first!");
      return;
    }

    setErrorMsg(null);
    setLoading(true);
    setTriageResult(null);
    setLoadingStage(0);
    setLongWait(false);

    let step = 0;
    const interval = setInterval(() => {
      step++;
      if (step < LOADING_STAGES.length) {
        setLoadingStage(step);
      } else {
        clearInterval(interval);
      }
    }, 1100);

    const longWaitTimer = setTimeout(() => setLongWait(true), 6000);

    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    try {
      const res = await submitTriage(requestText.trim(), jwtToken, abortRef.current.signal);

      if (res.status === 401) {
        logout();
        setIsModalOpen(true);
        clearInterval(interval);
        clearTimeout(longWaitTimer);
        setLongWait(false);
        setLoading(false);
        setErrorMsg("JWT Session expired or invalid. Please sign in again.");
        return;
      }

      if (res.ok) {
        const headerTime = res.headers.get("X-Process-Time");
        const data = await res.json();
        if (!data.process_time_ms && headerTime) {
          data.process_time_ms = parseFloat(headerTime);
        }

        clearInterval(interval);
        clearTimeout(longWaitTimer);
        setLongWait(false);
        setLoadingStage(LOADING_STAGES.length - 1);

        setTimeout(() => {
          setLoading(false);
          setTriageResult(data);
        }, 200);
        return;
      }

      const errData = await res.json().catch(() => ({}));
      clearInterval(interval);
      clearTimeout(longWaitTimer);
      setLongWait(false);
      setLoading(false);
      setErrorMsg(errData.detail || "Server request failed");
    } catch (err) {
      if (err.name === 'AbortError') return; // Silent on component unmount / cancellation
      clearInterval(interval);
      clearTimeout(longWaitTimer);
      setLongWait(false);
      setLoading(false);
      setErrorMsg(err.message || "Something went wrong. Please try again.");
    }
  };

  const currentStage = LOADING_STAGES[loadingStage] || LOADING_STAGES[0];

  return (
    <div ref={mainRef} className="min-h-screen flex flex-col justify-between selection:bg-[#FF5C00] selection:text-white relative bg-[#FFF8EE]">
      
      {/* Custom Cursor */}
      <CustomCursor />

      {/* Water Ripple Waves & Rainbow Powder Drops Canvas */}
      <WaterRippleCanvas />

      {/* Broken Glowing Glass Canvas Background */}
      <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0 opacity-60"></canvas>

      {/* Header Component */}
      <div className="gsap-header relative z-10">
        <Header
          jwtToken={jwtToken}
          onOpenLogin={() => setIsModalOpen(true)}
          onLogout={handleLogout}
        />
      </div>

      {/* Main Container */}
      <main className="max-w-4xl w-full mx-auto px-4 py-8 flex-1 space-y-8 relative z-10">
        
        {/* Input Section */}
        <div className="gsap-input-section">
          <TriageInput
            requestText={requestText}
            setRequestText={setRequestText}
            selectedMockIdx={selectedMockIdx}
            setSelectedMockIdx={setSelectedMockIdx}
            onSubmit={handleSubmitTriage}
            loading={loading}
          />
        </div>

        {/* Progressive Loader */}
        {loading && (
          <ProgressiveLoader
            stageText={currentStage.text}
            progressPct={currentStage.pct}
            longWait={longWait}
          />
        )}

        {/* Error Banner */}
        {errorMsg && (
          <div className="bg-rose-50 border-2 border-rose-200 text-rose-800 px-5 py-4 rounded-2xl text-sm flex items-center justify-between shadow-lg animate-in fade-in duration-200">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              <span className="font-semibold">{errorMsg}</span>
            </div>
            <button onClick={() => setErrorMsg(null)} className="text-rose-500 hover:text-rose-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Results Zone */}
        {triageResult && (
          <TriageResult
            result={triageResult}
            onCopyToast={showToast}
            jwtToken={jwtToken}
          />
        )}

      </main>

      {/* Footer */}
      <footer className="border-t-2 border-[#FFE0B2] py-6 text-xs font-bold text-[#7A6B63] bg-[#FFF8EE] relative z-10">
        <div className="max-w-4xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <p>© {new Date().getFullYear()} Node Solutions Inc. All Rights Reserved.</p>
          <p className="text-[11px] font-extrabold text-[#FF5C00] bg-[#FF5C00]/10 px-3.5 py-1 rounded-full border border-[#FF5C00]/30 shadow-sm">
            Enterprise AI Request Triage Platform
          </p>
        </div>
      </footer>

      {/* JWT Login Modal */}
      <JwtModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {/* Dedicated Toast Notification */}
      <Toast message={toastMsg} />

    </div>
  );
}

