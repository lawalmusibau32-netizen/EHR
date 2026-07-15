import { cn } from "@/lib/utils";

function Input({ className, type, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded-lg border border-border/50 bg-white/5 px-3 py-1 text-sm shadow-sm transition-all duration-300 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground/50 backdrop-blur-sm hover:border-border/80 focus-visible:outline-none focus-visible:border-primary/50 focus-visible:shadow-[0_0_0_2px_rgba(6,182,212,0.1),0_0_20px_rgba(6,182,212,0.05)] focus-visible:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

export { Input };
