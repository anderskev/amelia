/**
 * @fileoverview Utility functions for the dashboard application.
 */
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merges Tailwind CSS classes safely, handling conflicts.
 *
 * Combines multiple class values using clsx and resolves Tailwind
 * class conflicts using tailwind-merge.
 *
 * @param inputs - Class values to merge (strings, arrays, objects)
 * @returns Merged class string with conflicts resolved
 *
 * @example
 * ```ts
 * cn('px-4 py-2', 'px-6') // => 'py-2 px-6'
 * cn('text-red-500', { 'text-blue-500': isBlue })
 * ```
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formats ISO 8601 timestamp to HH:MM:SS format.
 *
 * Returns "-" for invalid or malformed timestamps to prevent render errors.
 *
 * @param isoString - ISO 8601 timestamp string
 * @returns Formatted time string (e.g., "10:30:45") or "-" if invalid
 *
 * @example
 * ```ts
 * formatTime('2025-12-13T10:30:45.123Z') // => '10:30:45'
 * formatTime('invalid') // => '-'
 * ```
 */
export function formatTime(isoString: string | null | undefined): string {
  if (!isoString) {
    return '-';
  }
  const date = new Date(isoString);
  if (!Number.isFinite(date.getTime())) {
    return '-';
  }
  return date.toISOString().slice(11, 19); // HH:MM:SS
}

/**
 * Formats driver string for display.
 *
 * Extracts the driver type (API or CLI) from the full driver string.
 *
 * @param driver - Driver string (e.g., "api:openrouter", "cli:claude")
 * @returns Formatted driver type (e.g., "API", "CLI")
 *
 * @example
 * ```ts
 * formatDriver('api:openrouter') // => 'API'
 * formatDriver('cli:claude') // => 'CLI'
 * ```
 */
export function formatDriver(driver: string): string {
  if (driver.startsWith('api:')) return 'API';
  if (driver.startsWith('cli:')) return 'CLI';
  return driver.toUpperCase();
}

/**
 * Formats model name for display.
 *
 * Capitalizes simple model names and formats longer model identifiers
 * with proper spacing and version numbers.
 *
 * @param model - Model identifier (e.g., "sonnet", "claude-3-5-sonnet")
 * @returns Formatted model name (e.g., "Sonnet", "Claude 3.5 Sonnet")
 *
 * @example
 * ```ts
 * formatModel('sonnet') // => 'Sonnet'
 * formatModel('claude-3-5-sonnet') // => 'Claude 3.5 Sonnet'
 * ```
 */
export function formatModel(model: string): string {
  // Handle simple names like "sonnet", "opus", "haiku"
  if (/^(sonnet|opus|haiku)$/i.test(model)) {
    return model.charAt(0).toUpperCase() + model.slice(1).toLowerCase();
  }
  // Handle longer model names - capitalize and clean up
  return model
    .split(/[-_]/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
    .replace(/(\d)(\d)/g, '$1.$2'); // "35" -> "3.5"
}
