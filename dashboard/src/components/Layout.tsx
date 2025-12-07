/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { Outlet, Link, useLocation, useNavigation } from 'react-router-dom';
import {
  GitBranch,
  History,
  Radio,
  Compass
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';
import { NavigationProgress } from '@/components/NavigationProgress';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useWorkflowStore } from '@/store/workflowStore';

export function Layout() {
  const location = useLocation();
  const navigation = useNavigation();

  // Initialize WebSocket connection
  useWebSocket();

  // Get connection status from store
  const isConnected = useWorkflowStore((state) => state.isConnected);

  const isNavigating = navigation.state !== 'idle';

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-sidebar-border">
          <h1 className="text-4xl font-display text-sidebar-primary tracking-wider">
            AMELIA
          </h1>
          <p className="text-xs font-mono text-muted-foreground mt-1">
            Agentic Orchestrator
          </p>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1">
          <nav className="p-4" aria-label="Main navigation">
            <div className="space-y-6">
              <NavSection title="WORKFLOWS">
                <NavLink
                  to="/workflows"
                  icon={<GitBranch className="w-4 h-4" />}
                  active={isActive('/workflows')}
                  label="Active Jobs"
                />
              </NavSection>

              <NavSection title="HISTORY">
                <NavLink
                  to="/history"
                  icon={<History className="w-4 h-4" />}
                  active={isActive('/history')}
                  label="Past Runs"
                />
              </NavSection>

              <NavSection title="MONITORING">
                <NavLink
                  to="/logs"
                  icon={<Radio className="w-4 h-4" />}
                  active={isActive('/logs')}
                  label="Logs"
                />
              </NavSection>
            </div>
          </nav>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center gap-3">
            <Compass className="w-8 h-8 text-muted-foreground/50" />
            <div className="text-xs font-mono text-muted-foreground">
              <div>Server: localhost:8420</div>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={cn(
                    'inline-block w-2 h-2 rounded-full',
                    isConnected
                      ? 'bg-[--status-running] animate-pulse-glow'
                      : 'bg-[--status-failed]'
                  )}
                />
                {isConnected ? 'Connected' : 'Disconnected'}
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content area with navigation progress */}
      <main className="flex-1 overflow-hidden relative">
        {isNavigating && <NavigationProgress />}
        <Outlet />
      </main>
    </div>
  );
}

// Helper components
interface NavSectionProps {
  title: string;
  children: React.ReactNode;
}

function NavSection({ title, children }: NavSectionProps) {
  return (
    <div>
      <div className="text-xs font-heading text-muted-foreground/60 font-semibold tracking-wider px-3 py-2">
        {title}
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

interface NavLinkProps {
  to: string;
  icon: React.ReactNode;
  active: boolean;
  label: string;
}

function NavLink({ to, icon, active, label }: NavLinkProps) {
  return (
    <Link
      to={to}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'flex items-center gap-3 px-3 py-2 font-heading font-semibold text-sm tracking-wide transition-colors focus-ring rounded',
        active
          ? 'bg-sidebar-primary text-sidebar-primary-foreground'
          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
      )}
    >
      {icon}
      {label}
    </Link>
  );
}
