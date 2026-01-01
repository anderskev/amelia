/**
 * @fileoverview Loader for the settings page.
 *
 * Fetches all prompts from the API for display in the settings page.
 */
import { api } from '@/api/client';
import type { PromptSummary } from '@/types';

/**
 * Data returned by the settings loader.
 */
export interface SettingsLoaderData {
  /** Array of prompt summaries grouped by agent. */
  prompts: PromptSummary[];
}

/**
 * Loader for the settings page.
 * Fetches all prompts from the API.
 *
 * @returns Object containing the list of prompts.
 * @throws {Error} When the API request fails.
 *
 * @example
 * ```typescript
 * const { prompts } = await settingsLoader();
 * const grouped = groupPromptsByAgent(prompts);
 * ```
 */
export async function settingsLoader(): Promise<SettingsLoaderData> {
  const prompts = await api.getPrompts();
  return { prompts };
}

/**
 * Groups prompts by agent name for display.
 *
 * @param prompts - Array of prompt summaries.
 * @returns Map of agent names to their prompts.
 *
 * @example
 * ```typescript
 * const grouped = groupPromptsByAgent(prompts);
 * // { architect: [prompt1], developer: [prompt2, prompt3], reviewer: [prompt4] }
 * ```
 */
export function groupPromptsByAgent(
  prompts: PromptSummary[]
): Record<string, PromptSummary[]> {
  return prompts.reduce(
    (acc, prompt) => {
      const agent = prompt.agent;
      if (!acc[agent]) {
        acc[agent] = [];
      }
      acc[agent].push(prompt);
      return acc;
    },
    {} as Record<string, PromptSummary[]>
  );
}
