/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

/**
 * Simple toast notification utilities.
 * In a real implementation, this would integrate with a toast library like react-hot-toast.
 * For now, we use console logging and could add a toast UI component later.
 */

export function success(message: string): void {
  console.log(`✓ ${message}`);
  // TODO: Integrate with toast UI library
}

export function error(message: string): void {
  console.error(`✗ ${message}`);
  // TODO: Integrate with toast UI library
}

export function info(message: string): void {
  console.info(`ℹ ${message}`);
  // TODO: Integrate with toast UI library
}
