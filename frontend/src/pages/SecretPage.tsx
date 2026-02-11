import { useState, useEffect } from "react";
import MammoniaLogo from "../components/MammoniaLogo";
import { Rocket, ArrowLeft, Sparkles, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function SecretPage() {
  const navigate = useNavigate();
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setRevealed(true), 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center relative">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/4 w-72 h-72 bg-accent-purple/10 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/3 right-1/4 w-64 h-64 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: "2s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent-gold/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: "1s" }} />
      </div>

      <div className={`relative z-10 text-center transition-all duration-1000 ${revealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
        {/* Glitch / Lock icon */}
        <div className="mb-8 flex justify-center">
          <div className="relative">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-accent-purple/20 to-primary-500/20 border border-accent-purple/30 flex items-center justify-center animate-float">
              <Lock size={32} className="text-accent-purple" />
            </div>
            <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-accent-gold/20 border border-accent-gold/30 flex items-center justify-center animate-pulse">
              <Sparkles size={12} className="text-accent-gold" />
            </div>
          </div>
        </div>

        <h1 className="text-4xl font-bold tracking-tight mb-3">
          <span className="text-gradient">You found it.</span>
        </h1>
        <p className="text-dark-400 text-lg mb-2 max-w-md mx-auto">
          Something new is coming...
        </p>
        <p className="text-dark-500 text-sm mb-10 max-w-sm mx-auto">
          This is a placeholder for the next project. Stay tuned.
        </p>

        {/* Teaser card */}
        <div className="glass p-8 max-w-sm mx-auto gradient-border mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Rocket size={24} className="text-primary-400" />
            <span className="text-xl font-bold text-gradient">Next Project</span>
          </div>
          <p className="text-dark-400 text-sm leading-relaxed">
            A new tool is being forged in the shadows. When it's ready, this page will be your gateway.
          </p>
          <div className="mt-6 flex items-center justify-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
            <div className="w-2 h-2 rounded-full bg-accent-purple animate-pulse" style={{ animationDelay: "0.3s" }} />
            <div className="w-2 h-2 rounded-full bg-accent-gold animate-pulse" style={{ animationDelay: "0.6s" }} />
          </div>
        </div>

        {/* Back button */}
        <button
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-2 text-dark-400 hover:text-primary-400 transition-colors text-sm group"
        >
          <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
          Back to Mammonia
        </button>
      </div>
    </div>
  );
}
