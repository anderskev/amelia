import { ReactNode } from 'react';
import { Chrome } from 'lucide-react';

interface BrowserCheckProps {
  children: ReactNode;
}

export function BrowserCheck({ children }: BrowserCheckProps) {
  // Check for Chrome (but not Edge or Opera)
  const isChrome =
    /Chrome/.test(navigator.userAgent) && !/Edg|OPR/.test(navigator.userAgent);

  if (!isChrome) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground p-8">
        <Chrome className="w-16 h-16 text-primary mb-4" />
        <h1 className="text-4xl font-display text-primary mb-4">
          Unsupported Browser
        </h1>
        <p className="text-muted-foreground mb-4 max-w-md text-center">
          Amelia Dashboard is optimized for Google Chrome.
        </p>
        <p className="text-muted-foreground mb-8 max-w-md text-center text-sm">
          Chrome-specific features: container queries, structuredClone(),
          native WebSocket ping/pong, CSS color-mix()
        </p>
        <a
          href="https://www.google.com/chrome/"
          className="text-accent hover:underline font-heading text-lg tracking-wide"
        >
          Download Chrome -&gt;
        </a>
      </div>
    );
  }

  return <>{children}</>;
}
