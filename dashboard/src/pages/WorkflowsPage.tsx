/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkflows } from '@/hooks/useWorkflows';
import { JobQueue } from '@/components/JobQueue';
import { WorkflowEmptyState } from '@/components/WorkflowEmptyState';

export default function WorkflowsPage() {
  const { workflows } = useWorkflows();
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    navigate(`/workflows/${id}`);
  };

  if (workflows.length === 0) {
    return <WorkflowEmptyState variant="no-workflows" />;
  }

  return (
    <JobQueue
      workflows={workflows}
      selectedId={selectedId}
      onSelect={handleSelect}
    />
  );
}

// Loader function will be added in Plan 09
// export async function loader() { ... }
