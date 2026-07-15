import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-ring/50 focus:ring-offset-2 backdrop-blur-sm",
  {
    variants: {
      variant: {
        default:
          "border-primary/30 bg-primary/15 text-primary shadow-[0_0_10px_rgba(6,182,212,0.1)]",
        secondary:
          "border-border/40 bg-secondary/50 text-secondary-foreground/80",
        destructive:
          "border-destructive/30 bg-destructive/15 text-destructive shadow-[0_0_10px_rgba(239,68,68,0.1)]",
        outline:
          "border-border/50 text-foreground/70 bg-transparent",
        success:
          "border-emerald-500/30 bg-emerald-500/15 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.1)]",
        warning:
          "border-amber-500/30 bg-amber-500/15 text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.1)]",
        info:
          "border-blue-500/30 bg-blue-500/15 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.1)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
