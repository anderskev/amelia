import { cn, formatDriver, formatModel } from "@/lib/utils";
import { Bot, Cpu, MessageSquare, Circle } from "lucide-react";
import type { ProfileInfo, SessionStatus, SessionUsageSummary } from "@/types/api";
import { Separator } from "@/components/ui/separator";

interface SessionInfoBarProps {
  profile: ProfileInfo | null;
  status: SessionStatus;
  messageCount: number;
  usageSummary?: SessionUsageSummary;
  className?: string;
}

const statusConfig: Record<SessionStatus, { label: string; color: string }> = {
  active: { label: "Active", color: "text-emerald-400" },
  ready_for_handoff: { label: "Ready", color: "text-amber-400" },
  completed: { label: "Done", color: "text-blue-400" },
  failed: { label: "Failed", color: "text-red-400" },
};

/**
 * Session info bar displaying model, driver, status and message count.
 *
 * Features a compact, information-dense layout with visual badges
 * for quick scanning of session context.
 */
export function SessionInfoBar({
  profile,
  status,
  messageCount,
  usageSummary,
  className,
}: SessionInfoBarProps) {
  const statusInfo = statusConfig[status];

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2 border-b border-border/50",
        "bg-gradient-to-r from-background via-muted/30 to-background",
        "text-xs font-mono",
        className
      )}
    >
      {/* Model + Driver Badge */}
      {profile && (
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-primary/10 border border-primary/20">
            <Bot className="h-3 w-3 text-primary" />
            <span className="text-foreground font-medium">
              {formatModel(profile.model)}
            </span>
          </div>
          <div className="flex items-center gap-1 px-1.5 py-1 rounded bg-muted/50">
            <Cpu className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground text-[10px] uppercase tracking-wider">
              {formatDriver(profile.driver)}
            </span>
          </div>
        </div>
      )}

      {/* Divider when profile exists */}
      {profile && <div className="h-4 w-px bg-border/50" />}

      {/* Status Indicator */}
      <div className="flex items-center gap-1.5">
        <Circle
          className={cn("h-2 w-2 fill-current", statusInfo.color)}
        />
        <span className={cn("text-muted-foreground", statusInfo.color)}>
          {statusInfo.label}
        </span>
      </div>

      {/* Message Count */}
      <div className="flex items-center gap-1 ml-auto text-muted-foreground">
        <MessageSquare className="h-3 w-3" />
        <span>{messageCount}</span>
      </div>

      {/* Cost Display - only show when cost > 0 */}
      {usageSummary && usageSummary.total_cost_usd > 0 && (
        <>
          <Separator orientation="vertical" className="h-3" />
          <span className="text-emerald-500/70 font-medium">
            ${usageSummary.total_cost_usd.toFixed(2)}
          </span>
        </>
      )}
    </div>
  );
}
