// components/Hero.tsx
"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
const ChatBox = dynamic(() => import("../components/chat/ChatBox"), { ssr: false });

export default function Hero() {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      if (!loaded) setError(true);
    }, 8000);
    return () => clearTimeout(t);
  }, [loaded]);

  return (
    <section id="hero" className="relative h-screen flex items-center justify-center px-6 overflow-hidden">
      {/* ---- iframe background (ensure it's visible) ---- */}
      <div
        className="absolute inset-0"
        style={{ zIndex: 0, pointerEvents: "none" /* iframe is bottom layer in hero */ }}
        aria-hidden
      >
        <iframe
          title="spline-3d-bg"
          src="https://my.spline.design/photorealearthanimationtoreveal-KJvwE3ZtKEyQIRtRLXbtu3Ok/"
          className="spline-iframe absolute inset-0 w-full h-full"
          frameBorder="0"
          loading="lazy"
          allow="accelerometer; autoplay; camera; gyroscope; picture-in-picture; fullscreen; xr-spatial-tracking"
          style={{
            opacity: loaded ? 1 : 0,
            transition: "opacity 600ms ease",
            background: "transparent",
            display: "block",
            width: "100%",
            height: "140%",
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            transform: "translateZ(-20%)"
          }}
          onLoad={() => {
            setLoaded(true);
            setError(false);
          }}
          onError={() => setError(true)}
        />
        {/* semi-transparent overlay - keep it light so spline shows */}
        <div
          className="absolute bottom-0 right-0 w-48 h-24 bg-black"
          style={{ zIndex: 10 }}
        />
        
      </div>

      {/* ---- hero content (above iframe) ---- */}
      <div className="relative z-20 w-full max-w-7xl text-center">
        <h1
          className="h-hero font-extrabold text-[140px] md:text-[180px] lg:text-[220px] leading-none text-white opacity-95 mx-auto"
          style={{ WebkitTextStroke: "0.5px rgba(255,255,255,0.06)", letterSpacing: "-0.02em" }}
        >
          Void
        </h1>

        <div className="mt-6">
          <ChatBox placeholder="What do you want to know?" />
        </div>

        <div className="mt-8 text-center text-sm text-slate-300 max-w-3xl mx-auto">
          VOID is a direct line to the answers of ocean data. No code, no waiting. Just ask.
        </div>
      </div>
    </section>
  );
}
