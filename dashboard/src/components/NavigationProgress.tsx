/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

export function NavigationProgress() {
  return (
    <div className="absolute top-0 left-0 right-0 h-1 bg-primary/20 z-50">
      <div
        className="h-full bg-primary transition-all duration-300"
        style={{ width: '30%', animation: 'progress-pulse 1s ease-in-out infinite' }}
      />
    </div>
  );
}
