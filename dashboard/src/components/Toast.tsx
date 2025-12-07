/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

/**
 * @fileoverview Toast notification utilities.
 *
 * Simple toast notification utilities for displaying user feedback.
 * Currently uses console logging; can be integrated with a toast
 * library like react-hot-toast or sonner in the future.
 */

/**
 * Displays a success toast notification.
 * @param message - Success message to display
 */
export function success(message: string): void {
  console.log(`✓ ${message}`);
  // TODO: Integrate with toast UI library
}

/**
 * Displays an error toast notification.
 * @param message - Error message to display
 */
export function error(message: string): void {
  console.error(`✗ ${message}`);
  // TODO: Integrate with toast UI library
}

/**
 * Displays an informational toast notification.
 * @param message - Info message to display
 */
export function info(message: string): void {
  console.info(`ℹ ${message}`);
  // TODO: Integrate with toast UI library
}
