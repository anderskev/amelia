import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardSidebar } from './DashboardSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { useDemoMode } from '@/hooks/useDemoMode';

// Mock the workflow store
vi.mock('@/store/workflowStore', () => ({
  useWorkflowStore: vi.fn((selector) => {
    const state = { isConnected: true, selectWorkflow: vi.fn() };
    return selector(state);
  }),
}));

// Mock the demo mode hook
vi.mock('@/hooks/useDemoMode', () => ({
  useDemoMode: vi.fn(() => ({ isDemo: false, demoType: null })),
}));

const renderSidebar = (initialRoute = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <SidebarProvider>
        <DashboardSidebar />
      </SidebarProvider>
    </MemoryRouter>
  );
};

describe('DashboardSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders branding', () => {
    renderSidebar();
    expect(screen.getByText('AMELIA')).toBeInTheDocument();
  });

  it.each([
    ['Active Jobs', '/workflows'],
    ['Past Runs', '/history'],
    ['Logs', '/logs'],
  ])('renders %s navigation link to %s', (label, href) => {
    renderSidebar();
    const link = screen.getByRole('link', { name: new RegExp(label) });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', href);
  });

  it('renders section labels', () => {
    renderSidebar();
    expect(screen.getByText('WORKFLOWS')).toBeInTheDocument();
    expect(screen.getByText('TOOLS')).toBeInTheDocument();
    expect(screen.getByText('IMPROVE')).toBeInTheDocument();
    expect(screen.getByText('USAGE')).toBeInTheDocument();
  });

  it('shows connected status when WebSocket is connected', () => {
    renderSidebar();
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('applies active styling to current route', () => {
    renderSidebar('/workflows');
    const link = screen.getByRole('link', { name: /Active Jobs/ });
    // NavLink sets aria-current="page" when active
    expect(link).toHaveAttribute('aria-current', 'page');
  });

  it('shows infinity symbol when in demo mode', () => {
    // Mock demo mode as active
    vi.mocked(useDemoMode).mockReturnValue({ isDemo: true, demoType: 'infinite' });

    renderSidebar();

    // Should show both AMELIA and infinity symbol
    expect(screen.getByText('AMELIA')).toBeInTheDocument();
    expect(screen.getByText('∞')).toBeInTheDocument();
  });

  it('shows AMELIA logo when not in demo mode', () => {
    // Mock demo mode as inactive (default)
    vi.mocked(useDemoMode).mockReturnValue({ isDemo: false, demoType: null });

    renderSidebar();

    // Should show AMELIA instead of infinity symbol
    expect(screen.getByText('AMELIA')).toBeInTheDocument();
  });
});
