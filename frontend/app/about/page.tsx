"use client";
import GlassCard from "../../components/GlassCard";
import { motion, HTMLMotionProps } from "framer-motion";

const MotionDiv = motion.div as React.FC<
  HTMLMotionProps<"div"> & React.HTMLAttributes<HTMLDivElement>
>;

export default function About() {
  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden text-white p-6">
      <section className="relative z-10 max-w-6xl mx-auto w-full">
        <MotionDiv
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="glass-card p-8 liquid-radius outline-1"
        >
          <p className="text-lg text-slate-300 leading-relaxed max-w-3xl mx-auto">
            We are scientists and researchers who were drowning in data.
            <br /><br />
            Our days were spent fighting code, not finding answers. We knew the discoveries were in there, buried under layers of technical nonsense. It was a colossal waste of time and brainpower.
            <br /><br />
            So we asked a simple question: What if you could just... talk to the data? What if the most powerful tool for exploration wasn't a script, but a sentence?
            <br /><br />
            That question became our obsession. It became Void.
            <br /><br />
            Our mission is to destroy the barrier between curiosity and discovery. We believe brilliant minds should be focused on brilliant questions, not on debugging code. We're building the tools we always wished we had.
            <br /><br />
            We're here to give science its time back.
          </p>
        </MotionDiv>
      </section>
    </main>
  );
}