import { useState, useCallback, useRef } from "react";
import { cn } from "@/lib/utils";
import { Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CopyButtonProps {
  content: string;
  className?: string;
}

/**
 * Copies text to clipboard with iOS fallback.
 *
 * iOS Safari has quirks with navigator.clipboard.writeText() in some contexts.
 * This function tries the modern API first, then falls back to execCommand.
 */
async function copyToClipboard(text: string): Promise<boolean> {
  // Try modern Clipboard API first
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fall through to fallback
    }
  }

  // Fallback for iOS and older browsers
  const textArea = document.createElement("textarea");
  textArea.value = text;

  // Prevent scrolling on iOS
  textArea.style.position = "fixed";
  textArea.style.left = "-9999px";
  textArea.style.top = "0";
  textArea.style.opacity = "0";

  document.body.appendChild(textArea);

  // iOS specific: need to select with setSelectionRange
  textArea.focus();
  textArea.setSelectionRange(0, text.length);

  let success = false;
  try {
    success = document.execCommand("copy");
  } catch {
    success = false;
  }

  document.body.removeChild(textArea);
  return success;
}

/**
 * Compact copy button for message bubbles.
 *
 * - Shows on hover on desktop
 * - Always visible on touch devices (mobile/iOS)
 * - Uses iOS-compatible clipboard handling
 */
export function CopyButton({ content, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopy = useCallback(async () => {
    const success = await copyToClipboard(content);
    if (success) {
      setCopied(true);
      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => setCopied(false), 2000);
    }
  }, [content]);

  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn(
        "h-6 w-6 shrink-0",
        "text-muted-foreground/50 hover:text-muted-foreground",
        "hover:bg-muted/50 transition-colors",
        // Desktop: show on hover via group-hover
        // Mobile: always visible (touch devices don't have hover)
        "opacity-0 group-hover:opacity-100 touch:opacity-100",
        className
      )}
      onClick={handleCopy}
      aria-label={copied ? "Copied" : "Copy message"}
    >
      {copied ? (
        <Check className="h-3 w-3 text-emerald-500" />
      ) : (
        <Copy className="h-3 w-3" />
      )}
    </Button>
  );
}
