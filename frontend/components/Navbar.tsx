"use client";
import Link from "next/link";
import { useState } from "react";
import clsx from "clsx";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const links = ["Home", "About",];

  return (
    <header className="w-full fixed top-2 left-0 z-20">
      <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between glass-card backdrop-blur-xl liquid-radius outline-1 shadow-figma-soft">
        {/* left - logo */}
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 flex items-center justify-center font-bold text-xl bg-white/6 liquid-radius glass-card">
            V
          </div>
        </div>

        {/* center - links */}
        <nav className="hidden md:flex gap-6 items-center">
          {links.map((l) => (
             <Link href={l === "About" ? "/about" : "/"} key={l} className="relative text-sm tracking-wider text-slate-300 hover:text-white">
               <span className="block h-[1px] bg-transparent group-hover:bg-white transition-all" />
               <span className="uppercase">{l}</span>
             </Link>
           ))}
        </nav>

        {/* right */}
        <div className="flex items-center gap-3">
          {/* <button className="px-4 py-2 text-sm rounded-full border border-white/10 backdrop-blur-md glass-card hover:scale-105 transition-transform">
            Sign in
          </button> */}
          <Link href="/chat" className="px-4 py-2 text-sm rounded-full border border-white/30 hover:scale-105 transition-transform liquid-radius glass-card">
            Try Void
          </Link>

          {/* mobile hamburger */}
          <button className="md:hidden ml-2" onClick={() => setOpen((v) => !v)} aria-label="menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-white/90">
              <path d="M4 7h16M4 12h16M4 17h16" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      {/* mobile menu */}
      {open && (
        <div className="md:hidden mt-2 max-w-7xl mx-auto px-6">
          <div className="glass-card p-4 rounded-xl">
            {["Grok","API","Company","Colossus","Careers","News"].map(l => (
              <a key={l} href="#" className="block py-2 text-sm uppercase tracking-wider">{l}</a>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
