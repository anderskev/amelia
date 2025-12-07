/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { Suspense } from 'react';
import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { router } from '@/router';

function GlobalLoadingSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export function App() {
  return (
    <TooltipProvider>
      <Suspense fallback={<GlobalLoadingSpinner />}>
        <RouterProvider router={router} />
      </Suspense>
      <Toaster richColors position="bottom-right" />
    </TooltipProvider>
  );
}
