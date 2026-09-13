import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function CustomCursor() {
  const dotRef = useRef(null);
  const ringRef = useRef(null);

  useEffect(() => {
    // Only enable custom cursor on non-touch devices
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) return;

    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;

    const pos = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    const mouse = { x: pos.x, y: pos.y };

    const handleMouseMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;

      // Move inner dot instantly
      gsap.to(dot, {
        x: mouse.x,
        y: mouse.y,
        duration: 0.08,
        ease: "power2.out"
      });

      // Move outer ring with smooth lag
      gsap.to(ring, {
        x: mouse.x,
        y: mouse.y,
        duration: 0.35,
        ease: "power3.out"
      });
    };

    const handleMouseDown = () => {
      gsap.to([dot, ring], { scale: 0.7, duration: 0.15 });
    };

    const handleMouseUp = () => {
      gsap.to([dot, ring], { scale: 1, duration: 0.15 });
    };

    // Magnetic expand on buttons & interactive elements
    const handleMouseOver = (e) => {
      const target = e.target.closest('button, input, textarea, a, select');
      if (target) {
        gsap.to(ring, { scale: 1.6, borderColor: '#FF5C00', backgroundColor: 'rgba(255, 92, 0, 0.08)', duration: 0.2 });
      } else {
        gsap.to(ring, { scale: 1, borderColor: 'rgba(255, 92, 0, 0.4)', backgroundColor: 'transparent', duration: 0.2 });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('mouseover', handleMouseOver);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mouseover', handleMouseOver);
    };
  }, []);

  return (
    <>
      {/* Inner Dot */}
      <div
        ref={dotRef}
        className="fixed top-0 left-0 w-3 h-3 -mt-1.5 -ml-1.5 rounded-full bg-[#FF5C00] pointer-events-none z-[9999] shadow-[0_0_12px_rgba(255,92,0,0.8)]"
      ></div>
      {/* Outer Lagging Ring */}
      <div
        ref={ringRef}
        className="fixed top-0 left-0 w-9 h-9 -mt-4.5 -ml-4.5 rounded-full border-2 border-[#FF5C00]/40 pointer-events-none z-[9998] transition-colors"
      ></div>
    </>
  );
}
