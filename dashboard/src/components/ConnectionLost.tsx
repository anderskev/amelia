/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ConnectionLostProps {
  onRetry: () => void;
  error?: string;
}

export function ConnectionLost({ onRetry, error }: ConnectionLostProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground p-8">
      <WifiOff className="w-16 h-16 text-destructive mb-4" />
      <h1 className="text-4xl font-display text-destructive mb-4">
        Connection Lost
      </h1>
      {error && (
        <p className="text-muted-foreground text-sm mb-8 max-w-md text-center">
          {error}
        </p>
      )}
      <Button onClick={onRetry}>
        <RefreshCw className="w-4 h-4" />
        Reconnect
      </Button>
    </div>
  );
}
