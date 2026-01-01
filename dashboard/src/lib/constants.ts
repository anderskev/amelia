/**
 * @fileoverview Application-wide constants and configuration values.
 *
 * Centralizes version info and other constants derived from package.json.
 */

import packageJson from '../../package.json';

/** Current application version from package.json. */
export const APP_VERSION = packageJson.version;

/** Style mapping for different agent types in activity logs and UI. */
export const AGENT_STYLES: Record<string, { text: string; bg: string }> = {
  PM: { text: 'text-agent-pm', bg: 'bg-agent-pm-bg' },
  ORCHESTRATOR: { text: 'text-muted-foreground', bg: '' },
  ARCHITECT: { text: 'text-agent-architect', bg: 'bg-agent-architect-bg' },
  DEVELOPER: { text: 'text-agent-developer', bg: 'bg-agent-developer-bg' },
  REVIEWER: { text: 'text-agent-reviewer', bg: 'bg-agent-reviewer-bg' },
  SYSTEM: { text: 'text-muted-foreground', bg: '' },
};
