export const dynamic = "force-dynamic";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5 animate-gradient-drift" />

      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <svg className="absolute w-full h-full opacity-[0.03]" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <pattern id="grid" width="8" height="8" patternUnits="userSpaceOnUse">
              <path d="M 8 0 L 0 0 0 8" fill="none" stroke="currentColor" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#grid)" />
        </svg>
      </div>

      <div className="absolute w-[500px] h-[500px] rounded-full bg-primary/10 blur-[150px] animate-breathe" style={{ top: "-10%", left: "-5%" }} />
      <div className="absolute w-[400px] h-[400px] rounded-full bg-emerald-500/10 blur-[120px] animate-breathe" style={{ bottom: "-8%", right: "-5%", animationDelay: "-2s" }} />
      <div className="absolute w-[300px] h-[300px] rounded-full bg-cyan-500/8 blur-[100px] animate-breathe" style={{ top: "40%", right: "15%", animationDelay: "-4s" }} />

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
        <div className="absolute -top-20 -left-20 w-40 h-40 border border-primary/20 rounded-[40%_60%_30%_70%_/_50%_40%_60%_50%] animate-morph opacity-20" style={{ animationDuration: "10s" }} />
        <div className="absolute -bottom-10 -right-10 w-48 h-48 border border-emerald-500/20 rounded-[30%_70%_50%_50%_/_60%_40%_70%_30%] animate-morph opacity-15" style={{ animationDuration: "12s", animationDelay: "-3s" }} />
      </div>

      <div className="absolute w-24 h-24 border-2 border-primary/20 rounded-xl -rotate-12 animate-float opacity-30" style={{ top: "12%", left: "10%", animationDuration: "8s" }} />
      <div className="absolute w-16 h-16 border-2 border-emerald-500/20 rounded-full animate-float opacity-25" style={{ bottom: "20%", left: "15%", animationDuration: "10s", animationDelay: "-3s" }} />
      <div className="absolute w-20 h-20 border-2 border-cyan-500/20 rotate-45 animate-float opacity-20" style={{ top: "25%", right: "12%", animationDuration: "9s", animationDelay: "-1s" }} />
      <div className="absolute w-12 h-12 bg-primary/10 rounded-lg rotate-[30deg] animate-float opacity-30" style={{ bottom: "30%", right: "20%", animationDuration: "11s", animationDelay: "-5s" }} />
      <div className="absolute w-32 h-32 border border-primary/10 rounded-full animate-float opacity-15" style={{ top: "60%", left: "5%", animationDuration: "7s", animationDelay: "-2s" }} />
      <div className="absolute w-8 h-8 bg-emerald-500/10 rounded-full animate-float opacity-40" style={{ top: "15%", right: "30%", animationDuration: "12s", animationDelay: "-4s" }} />
      <div className="absolute w-14 h-14 border border-cyan-500/15 rounded-xl rotate-[60deg] animate-float opacity-25" style={{ bottom: "15%", left: "30%", animationDuration: "9s", animationDelay: "-6s" }} />
      <div className="absolute w-10 h-10 bg-cyan-500/8 rounded-lg animate-float opacity-35" style={{ top: "45%", left: "20%", animationDuration: "8s", animationDelay: "-1.5s" }} />
      <div className="absolute w-28 h-[2px] bg-gradient-to-r from-transparent via-primary/30 to-transparent rounded-full animate-float opacity-40" style={{ top: "35%", left: "5%", animationDuration: "6s", animationDelay: "-3s" }} />
      <div className="absolute w-28 h-[2px] bg-gradient-to-r from-transparent via-emerald-500/25 to-transparent rounded-full animate-float opacity-35" style={{ top: "70%", right: "8%", animationDuration: "7s", animationDelay: "-1s" }} />

      <div className="relative w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <div className="relative inline-flex mb-6">
            <div className="absolute -inset-3 rounded-2xl bg-gradient-to-br from-primary/30 via-cyan-500/20 to-emerald-500/20 blur-xl animate-pulse-glow" />
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-primary-foreground font-bold text-xl shadow-xl shadow-primary/20 ring-1 ring-primary/20">
              H
            </div>
          </div>
          <h1 className="text-3xl font-bold">
            <span className="text-gradient">EHR</span>
          </h1>
          <p className="text-sm text-muted-foreground/60 mt-1 tracking-wide">Electronic Health Record System</p>
        </div>
        <div className="rounded-2xl border border-border/40 bg-card/60 backdrop-blur-2xl shadow-[0_8px_60px_rgba(0,0,0,0.3)] p-8 animate-slide-up relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-primary/5 rounded-full blur-[60px]" />
          <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-emerald-500/5 rounded-full blur-[60px]" />
          {children}
        </div>
      </div>
    </div>
  );
}
