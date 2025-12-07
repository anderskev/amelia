/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

/**
 * @fileoverview Main workflows listing page with canvas visualization.
 *
 * Displays the active workflow's pipeline canvas at the top with
 * job queue and activity log in a split view below.
 */
import { useState } from 'react';
import { useLoaderData, useFetcher } from 'react-router-dom';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { WorkflowEmptyState } from '@/components/WorkflowEmptyState';
import { PageHeader } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { WorkflowCanvas } from '@/components/WorkflowCanvas';
import { ActivityLog } from '@/components/ActivityLog';
import { ActivityLogSkeleton } from '@/components/ActivityLogSkeleton';
import { JobQueue } from '@/components/JobQueue';
import { getActiveWorkflow } from '@/utils/workflow';
import { buildPipeline } from '@/utils/pipeline';
import type { workflowsLoader, workflowDetailLoader } from '@/loaders/workflows';

/**
 * Displays workflow canvas and job queue with activity log.
 *
 * Layout:
 * - Top: Workflow header and pipeline canvas (full width)
 * - Bottom: Job queue (1/3) and activity log (2/3) side by side
 *
 * The active workflow is determined by priority:
 * 1. Running workflow (status === 'in_progress')
 * 2. Most recently started completed workflow
 *
 * @returns The workflows page UI
 */
export default function WorkflowsPage() {
  const { workflows, activeDetail } = useLoaderData<typeof workflowsLoader>();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const fetcher = useFetcher<typeof workflowDetailLoader>();

  // Auto-select active workflow
  const activeWorkflow = getActiveWorkflow(workflows);
  const displayedId = selectedId ?? activeWorkflow?.id ?? null;

  // Determine which detail to show:
  // 1. If user selected a different workflow and fetcher has data, use fetcher data
  // 2. If displaying the active workflow, use pre-loaded activeDetail
  // 3. Otherwise show loading state
  const isLoadingDetail = fetcher.state !== 'idle';
  let detail = null;
  if (selectedId && fetcher.data?.workflow) {
    detail = fetcher.data.workflow;
  } else if (displayedId === activeWorkflow?.id) {
    detail = activeDetail;
  }

  // Fetch detail when user selects a different workflow
  // NOTE: Uses existing /workflows/:id route and workflowDetailLoader
  const handleSelect = (id: string | null) => {
    setSelectedId(id);
    if (id && id !== activeWorkflow?.id) {
      fetcher.load(`/workflows/${id}`);
    }
  };

  if (workflows.length === 0) {
    return <WorkflowEmptyState variant="no-workflows" />;
  }

  // Build pipeline for canvas visualization
  const pipeline = detail ? buildPipeline(detail) : null;

  return (
    <div className="flex flex-col h-full w-full relative overflow-hidden">
      {/* Starfield background */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-40"
        style={{
          background: `
            radial-gradient(1px 1px at 20px 30px, rgb(239 248 226), transparent),
            radial-gradient(1px 1px at 40px 70px, rgb(239 248 226 / 0.8), transparent),
            radial-gradient(1px 1px at 50px 160px, rgb(239 248 226 / 0.6), transparent),
            radial-gradient(1px 1px at 90px 40px, rgb(239 248 226), transparent),
            radial-gradient(1px 1px at 130px 80px, rgb(239 248 226 / 0.7), transparent),
            radial-gradient(1.5px 1.5px at 160px 120px, rgb(255 200 87), transparent),
            radial-gradient(1px 1px at 200px 50px, rgb(239 248 226 / 0.5), transparent),
            radial-gradient(1px 1px at 280px 20px, rgb(239 248 226 / 0.6), transparent),
            radial-gradient(1.5px 1.5px at 320px 100px, rgb(91 155 213 / 0.8), transparent),
            radial-gradient(1px 1px at 400px 60px, rgb(239 248 226), transparent),
            radial-gradient(1.5px 1.5px at 550px 90px, rgb(255 200 87), transparent),
            radial-gradient(1px 1px at 650px 50px, rgb(239 248 226 / 0.9), transparent)
          `,
          backgroundRepeat: 'repeat',
          backgroundSize: '700px 180px',
        }}
        aria-hidden="true"
      />

      {/* Cockpit glass scanlines */}
      <div
        className="fixed inset-0 pointer-events-none z-[100]"
        style={{
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgb(239 248 226 / 0.01) 2px, rgb(239 248 226 / 0.01) 4px)',
        }}
        aria-hidden="true"
      />

      {/* Vignette */}
      <div
        className="fixed inset-0 pointer-events-none z-[99]"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 30%, rgb(13 26 18 / 0.6) 100%)',
        }}
        aria-hidden="true"
      />

      {/* Top: Header + Canvas (full width) */}
      <PageHeader>
        <PageHeader.Left>
          <PageHeader.Label>WORKFLOW</PageHeader.Label>
          <div className="flex items-center gap-3">
            <PageHeader.Title>{detail?.issue_id ?? 'SELECT JOB'}</PageHeader.Title>
            {detail?.worktree_name && (
              <PageHeader.Subtitle>{detail.worktree_name}</PageHeader.Subtitle>
            )}
          </div>
        </PageHeader.Left>
        <PageHeader.Center>
          <PageHeader.Label>ELAPSED</PageHeader.Label>
          <PageHeader.Value glow>--:--</PageHeader.Value>
        </PageHeader.Center>
        {detail && (
          <PageHeader.Right>
            {detail.status === 'in_progress' && (
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(255,200,87,0.6)]" />
            )}
            <StatusBadge status={detail.status} />
          </PageHeader.Right>
        )}
      </PageHeader>
      <Separator />
      {pipeline && <WorkflowCanvas pipeline={pipeline} />}

      {/* Bottom: Queue + Activity (split) - ScrollArea provides overflow handling */}
      <div className="flex-1 grid grid-cols-[320px_1fr] gap-4 p-4 overflow-hidden relative z-10">
        <ScrollArea className="h-full">
          <JobQueue
            workflows={workflows}
            selectedId={displayedId}
            onSelect={handleSelect}
          />
        </ScrollArea>
        <ScrollArea className="h-full">
          {detail ? (
            <ActivityLog workflowId={detail.id} initialEvents={detail.recent_events} />
          ) : isLoadingDetail ? (
            <ActivityLogSkeleton />
          ) : null}
        </ScrollArea>
      </div>
    </div>
  );
}
