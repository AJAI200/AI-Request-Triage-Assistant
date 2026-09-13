import React, { useEffect, useRef } from 'react';
import { useCanvasSize } from '../hooks/useCanvasSize';

// UI Design Aligned Star Palette
const UI_STAR_COLORS = [
  '#FF5C00', // Signature Vibrant Orange
  '#FFB703', // Golden Amber Sun
  '#EC4899', // Bright Pink
  '#84CC16', // Vibrant Lime Green
  '#8B5CF6', // Soft Violet
  '#FF8C42', // Warm Coral
  '#FFD166'  // Warm Starlight Yellow
];

// Helper to draw a 5-point star path
function drawStar(ctx, cx, cy, spikes, outerRadius, innerRadius, rotation = 0) {
  let rot = (Math.PI / 2) * 3 + rotation;
  let x = cx;
  let y = cy;
  const step = Math.PI / spikes;

  ctx.beginPath();
  ctx.moveTo(cx + Math.cos(rot) * outerRadius, cy + Math.sin(rot) * outerRadius);
  for (let i = 0; i < spikes; i++) {
    x = cx + Math.cos(rot) * outerRadius;
    y = cy + Math.sin(rot) * outerRadius;
    ctx.lineTo(x, y);
    rot += step;

    x = cx + Math.cos(rot) * innerRadius;
    y = cy + Math.sin(rot) * innerRadius;
    ctx.lineTo(x, y);
    rot += step;
  }
  ctx.lineTo(cx + Math.cos((Math.PI / 2) * 3 + rotation) * outerRadius, cy + Math.sin((Math.PI / 2) * 3 + rotation) * outerRadius);
  ctx.closePath();
}

const MAX_PARTICLES = 150;
const SPAWN_INTERVAL_MS = 40;

export default function WaterRippleCanvas() {
  const canvasRef = useRef(null);
  useCanvasSize(canvasRef);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const ripples = [];
    const particles = [];
    let hueIndex = 0;
    let lastSpawn = 0;

    const handleMouseMove = (e) => {
      const now = performance.now();
      if (now - lastSpawn < SPAWN_INTERVAL_MS) return;
      lastSpawn = now;

      const x = e.clientX;
      const y = e.clientY;

      if (ripples.length < 50) {
        ripples.push({
          x,
          y,
          radius: 4,
          maxRadius: 35 + Math.random() * 25,
          alpha: 0.4,
          color: UI_STAR_COLORS[hueIndex % UI_STAR_COLORS.length]
        });
      }

      for (let i = 0; i < 3; i++) {
        if (particles.length >= MAX_PARTICLES) break;
        const color = UI_STAR_COLORS[(hueIndex + i) % UI_STAR_COLORS.length];
        particles.push({
          x: x + (Math.random() - 0.5) * 18,
          y: y + Math.random() * 8,
          vx: (Math.random() - 0.5) * 1.0,
          vy: Math.random() * 1.6 + 0.8,
          size: Math.random() * 4 + 3.5,
          alpha: 0.9,
          rotation: Math.random() * Math.PI * 2,
          rotSpeed: (Math.random() - 0.5) * 0.1,
          color
        });
      }

      hueIndex++;
    };

    window.addEventListener('mousemove', handleMouseMove);

    let animId;
    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = ripples.length - 1; i >= 0; i--) {
        const r = ripples[i];
        r.radius += 1.4;
        r.alpha -= 0.015;

        if (r.alpha <= 0 || r.radius >= r.maxRadius) {
          ripples.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.beginPath();
        ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
        ctx.strokeStyle = r.color;
        ctx.globalAlpha = r.alpha;
        ctx.lineWidth = 1.6;
        ctx.stroke();
        ctx.restore();
      }

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.12;
        p.rotation += p.rotSpeed;
        p.size *= 0.975;
        p.alpha -= 0.022;

        if (p.alpha <= 0 || p.size <= 0.8) {
          particles.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.shadowBlur = 10;
        ctx.shadowColor = p.color;

        drawStar(ctx, p.x, p.y, 5, p.size, p.size * 0.45, p.rotation);
        ctx.fill();
        ctx.restore();
      }

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
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('visibilitychange', handleVisibility);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-40"
    ></canvas>
  );
}

