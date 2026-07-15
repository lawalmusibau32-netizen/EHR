"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LogIn, Eye, EyeOff, User, Lock, AlertCircle } from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<"username" | "password" | null>(null);
  const usernameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => usernameRef.current?.focus(), 100);
    return () => clearTimeout(timer);
  }, []);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const form = new FormData(e.currentTarget);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password"),
      }),
    });

    if (!res.ok) {
      const data = await res.json();
      setError(data.error ?? "Login failed.");
      setLoading(false);
      return;
    }

    const redirect = searchParams.get("redirect") ?? "/dashboard";
    router.push(redirect);
    router.refresh();
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-1">
        <h2 className="text-xl font-semibold tracking-tight">Welcome Back</h2>
        <p className="text-sm text-muted-foreground/50">Sign in to access your dashboard</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {error && (
          <div className="flex items-start gap-2.5 rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive shadow-[0_0_20px_rgba(239,68,68,0.06)] animate-slide-up">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="username" className="text-xs font-medium text-muted-foreground/60 tracking-wide uppercase">Username</Label>
          <div className="relative">
            <div className={`absolute inset-0 rounded-xl bg-gradient-to-r from-primary/20 via-cyan-500/10 to-transparent opacity-0 transition-opacity duration-500 ${focusedField === "username" ? "opacity-100" : ""}`} />
            <div className="relative flex items-center">
              <User className={`absolute left-3.5 h-4 w-4 transition-all duration-300 ${focusedField === "username" ? "text-primary" : "text-muted-foreground/30"}`} />
              <Input
                id="username"
                name="username"
                ref={usernameRef}
                required
                autoFocus={false}
                onFocus={() => setFocusedField("username")}
                onBlur={() => setFocusedField(null)}
                className="glass-input pl-10 h-11 rounded-xl text-sm placeholder:text-muted-foreground/25"
                placeholder="Enter your username"
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className="text-xs font-medium text-muted-foreground/60 tracking-wide uppercase">Password</Label>
            <span className="text-[11px] text-muted-foreground/30 hover:text-primary/60 cursor-default transition-colors duration-300">Forgot password?</span>
          </div>
          <div className="relative">
            <div className={`absolute inset-0 rounded-xl bg-gradient-to-r from-primary/20 via-cyan-500/10 to-transparent opacity-0 transition-opacity duration-500 ${focusedField === "password" ? "opacity-100" : ""}`} />
            <div className="relative flex items-center">
              <Lock className={`absolute left-3.5 h-4 w-4 transition-all duration-300 ${focusedField === "password" ? "text-primary" : "text-muted-foreground/30"}`} />
              <Input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                required
                onFocus={() => setFocusedField("password")}
                onBlur={() => setFocusedField(null)}
                className="glass-input pl-10 pr-10 h-11 rounded-xl text-sm placeholder:text-muted-foreground/25"
                placeholder="Enter your password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className={`absolute right-3.5 transition-all duration-300 ${focusedField === "password" ? "text-primary/70" : "text-muted-foreground/30"} hover:text-muted-foreground/60`}
                tabIndex={-1}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>

        <Button
          type="submit"
          className="relative w-full h-11 rounded-xl overflow-hidden group"
          disabled={loading}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-primary via-cyan-500 to-primary bg-[length:200%_100%] animate-shimmer opacity-90 group-hover:opacity-100 transition-opacity" />
          <span className="relative flex items-center justify-center gap-2 font-medium">
            {loading ? (
              <>
                <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                <span>Signing in</span>
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                <span>Sign In</span>
              </>
            )}
          </span>
        </Button>

        <p className="text-center text-[11px] text-muted-foreground/25 tracking-wider uppercase select-none">
          Electronic Health Record System v2.0
        </p>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-12">
        <span className="h-5 w-5 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
