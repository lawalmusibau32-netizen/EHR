import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  label: string;
  value: number | string;
  tone?: "default" | "success" | "warning" | "info" | "primary";
}

const toneStyles: Record<string, string> = {
  default: "text-foreground",
  success: "text-emerald-600 dark:text-emerald-400",
  warning: "text-amber-600 dark:text-amber-400",
  info: "text-blue-600 dark:text-blue-400",
  primary: "text-primary",
};

export function StatsCard({ label, value, tone = "default" }: StatsCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-muted-foreground mb-1">{label}</div>
        <div className={cn("text-2xl font-bold", toneStyles[tone])}>{value}</div>
      </CardContent>
    </Card>
  );
}
