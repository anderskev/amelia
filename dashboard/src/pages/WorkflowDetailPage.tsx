/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

/**
 * @fileoverview Workflow detail page with full status display.
 */
import { useLoaderData } from 'react-router-dom';
import { PageHeader } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { WorkflowProgress } from '@/components/WorkflowProgress';
import { ActivityLog } from '@/components/ActivityLog';
import { ApprovalControls } from '@/components/ApprovalControls';
import { WorkflowCanvas } from '@/components/WorkflowCanvas';
import { buildPipeline } from '@/utils/pipeline';
import type { WorkflowDetail } from '@/types';

/**
 * Data shape returned by the route loader.
 * @property workflow - Full workflow details
 */
interface LoaderData {
  workflow: WorkflowDetail;
}

/**
 * Displays comprehensive workflow details with progress, pipeline, and activity.
 *
 * Shows header with status, progress bar, visual pipeline canvas,
 * approval controls (when blocked), and real-time activity log.
 * Converts plan tasks to pipeline nodes for visualization.
 *
 * @returns The workflow detail page UI
 */
export default function WorkflowDetailPage() {
  const { workflow } = useLoaderData() as LoaderData;

  // Calculate progress from plan tasks
  const completedTasks = workflow.plan?.tasks.filter(t => t.status === 'completed').length || 0;
  const totalTasks = workflow.plan?.tasks.length || 0;

  // Check if workflow needs approval (blocked status)
  const needsApproval = workflow.status === 'blocked';

  // Generate plan summary for approval controls
  const planSummary = workflow.plan
    ? `Plan with ${workflow.plan.tasks.length} tasks`
    : 'No plan available';

  // Convert plan to pipeline format for WorkflowCanvas
  const pipeline = buildPipeline(workflow);

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <PageHeader>
        <PageHeader.Left>
          <PageHeader.Label>WORKFLOW</PageHeader.Label>
          <div className="flex items-center gap-3">
            <PageHeader.Title>{workflow.issue_id}</PageHeader.Title>
            <PageHeader.Subtitle>{workflow.worktree_name}</PageHeader.Subtitle>
          </div>
        </PageHeader.Left>
        <PageHeader.Center>
          <PageHeader.Label>ELAPSED</PageHeader.Label>
          <PageHeader.Value glow>--:--</PageHeader.Value>
        </PageHeader.Center>
        <PageHeader.Right>
          {workflow.status === 'in_progress' && (
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(255,200,87,0.6)]" />
          )}
          <StatusBadge status={workflow.status} />
        </PageHeader.Right>
      </PageHeader>

      {/* Main content area */}
      <div className="flex-1 overflow-hidden grid grid-cols-2 gap-4 p-6">
        {/* Left column: Progress, Canvas, and Approval Controls */}
        <div className="flex flex-col gap-4 overflow-y-auto">
          {/* Progress */}
          <div className="p-4 border border-border rounded-lg bg-card/50">
            <h3 className="font-heading text-xs font-semibold tracking-widest text-muted-foreground mb-3">
              PROGRESS
            </h3>
            <WorkflowProgress completed={completedTasks} total={totalTasks} />
          </div>

          {/* Workflow Canvas (visual pipeline) */}
          {pipeline && (
            <div className="p-4 border border-border rounded-lg bg-card/50">
              <h3 className="font-heading text-xs font-semibold tracking-widest text-muted-foreground mb-3">
                PIPELINE
              </h3>
              <WorkflowCanvas pipeline={pipeline} />
            </div>
          )}

          {/* Approval Controls (only shown when blocked) */}
          {needsApproval && (
            <ApprovalControls
              workflowId={workflow.id}
              planSummary={planSummary}
              status="pending"
            />
          )}
        </div>

        {/* Right column: Activity Log */}
        <div className="border border-border rounded-lg bg-card/50 overflow-hidden">
          <ActivityLog
            workflowId={workflow.id}
            initialEvents={workflow.recent_events}
          />
        </div>
      </div>
    </div>
  );
}

// Loader function will be added in Plan 09
// export async function loader({ params }) { ... }
