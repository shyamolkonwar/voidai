export default function Footer() {
  return (
    <footer className="mt-24 py-12">
      <div className="max-w-7xl mx-auto px-6 glass-card p-6 liquid-radius outline-1 shadow-figma-soft">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div>
            <div className="flex items-center gap-4">
          <div className="w-10 h-10 flex items-center justify-center font-bold text-xl bg-white/6 liquid-radius glass-card">
            V
          </div>
        </div>
          </div>
          <div className="flex gap-4">
            <a href="#" className="text-sm uppercase tracking-wider">Twitter</a>
            <a href="#" className="text-sm uppercase tracking-wider">Github</a>
            <a href="#" className="text-sm uppercase tracking-wider">LinkedIn</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
