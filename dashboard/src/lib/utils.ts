import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes safely, handling conflicts.
 * Use this for all dynamic class combinations.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
