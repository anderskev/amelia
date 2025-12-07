import { api } from '@/api/client';
import type { ActionFunctionArgs } from 'react-router-dom';
import type { ActionResult } from '@/types/api';

export async function approveAction({ params }: ActionFunctionArgs): Promise<ActionResult> {
  if (!params.id) {
    throw new Response('Workflow ID required', { status: 400 });
  }

  await api.approveWorkflow(params.id);
  return { success: true, action: 'approved' };
}

export async function rejectAction({ params, request }: ActionFunctionArgs): Promise<ActionResult> {
  if (!params.id) {
    throw new Response('Workflow ID required', { status: 400 });
  }

  const formData = await request.formData();
  const feedback = formData.get('feedback') as string;

  await api.rejectWorkflow(params.id, feedback);
  return { success: true, action: 'rejected' };
}

export async function cancelAction({ params }: ActionFunctionArgs): Promise<ActionResult> {
  if (!params.id) {
    throw new Response('Workflow ID required', { status: 400 });
  }

  await api.cancelWorkflow(params.id);
  return { success: true, action: 'cancelled' };
}
