/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes safely, handling conflicts.
 * Use this for all dynamic class combinations.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
