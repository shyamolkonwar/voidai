"use client";
import Hero from "../components/Hero";
import GlassCard from "../components/GlassCard";
import Footer from "../components/Footer";
import { motion, HTMLMotionProps } from "framer-motion";
import { useEffect, useState } from "react";

const MotionDiv = motion.div as React.FC<
  HTMLMotionProps<"div"> & React.HTMLAttributes<HTMLDivElement>
>;

// Animated text component for dramatic reveal
const AnimatedText = ({ text, className = "" }: { text: string; className?: string }) => {
  const [displayText, setDisplayText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, 50); // Speed of typing effect
      return () => clearTimeout(timer);
    }
  }, [currentIndex, text]);

  return (
    <span className={className}>
      {displayText}
      {currentIndex < text.length && (
        <span className="animate-pulse inline-block w-1 h-6 bg-red-500 ml-1 align-middle" />
      )}
    </span>
  );
};

// Staggered reveal for paragraph text
const StaggeredText = ({ text, className = "" }: { text: string; className?: string }) => {
  const words = text.split(" ");
  const [visibleWords, setVisibleWords] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleWords(prev => Math.min(prev + 1, words.length));
    }, 80); // Speed of word reveal
    return () => clearInterval(interval);
  }, [words.length]);

  return (
    <p className={className}>
      {words.map((word, index) => (
        <motion.span
          key={index}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: index < visibleWords ? 1 : 0, y: index < visibleWords ? 0 : 10 }}
          transition={{ duration: 0.3 }}
          className="inline-block mr-1"
        >
          {word}
        </motion.span>
      ))}
    </p>
  );
};

export default function Home() {
  return (
    <>
      {/* Hero Section */}
      <Hero />

      {/* Features & About Section */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 pb-28">
        {/* SECTION 2: THE PROBLEM - Converted to 3 cards */}
        <MotionDiv
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="mt-16 text-center"
        >
          <h2 className="text-3xl font-bold mb-12">YOUR DATA IS A HOSTAGE.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <GlassCard
              title="TRAPPED DATA"
              desc="Ocean data locked in outdated, incompatible formats that require specialized tools and expertise to access."
            />
            <GlassCard
              title="WAITING GAME"
              desc="Days of waiting for data scientists to run scripts. Your questions get stuck in endless queues and backlogs."
            />
            <GlassCard
              title="EXPERTISE BARRIER"
              desc="Requires PhD-level coding skills just to ask simple questions. The technical barrier excludes most researchers."
            />
          </div>
        </MotionDiv>

        {/* SECTION 3: THE SOLUTION & FEATURES */}
        <MotionDiv
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="mt-16 text-center"
        >
          <h2 className="text-3xl font-bold mb-12">THE OLD WAY IS BROKEN. THIS IS THE NEW STANDARD.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <GlassCard
              title="SPEAK ENGLISH, NOT CODE"
              desc="Ask questions in plain English and get immediate answers. No coding required."
            />
            <GlassCard
              title="SEE. DON'T GUESS"
              desc="Get instant visualizations and insights from your data without technical barriers."
            />
            <GlassCard
              title="SHARE. DON'T HOARD"
              desc="Collaborate seamlessly with your team and share discoveries in real-time."
            />
          </div>
        </MotionDiv>

        

        {/* SECTION 4: FINAL CALL TO ACTION */}
        <MotionDiv
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="mt-16 glass-card p-8 liquid-radius outline-1 text-center"
        >
          <h2 className="text-3xl font-bold mb-4">THE OCEAN IS TALKING. ARE YOU LISTENING?</h2>
          <p className="text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto">
            The answers are already in your data. Stop digging through code and start asking questions.
            Your next discovery awaits.
          </p>
        </MotionDiv>
      </section>
            
                  <Footer />
                </>
              );
            }
