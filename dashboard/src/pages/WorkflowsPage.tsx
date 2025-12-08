/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { Loader2 } from 'lucide-react';

export default function WorkflowsPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
      <h2 className="text-3xl font-display text-primary">Active Workflows</h2>
      <p className="text-muted-foreground font-heading text-lg tracking-wide">
        Coming soon
      </p>
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

// Loader function will be added in Plan 09
// export async function loader() { ... }
