import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardSidebar } from './DashboardSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';

const renderSidebar = () => {
  return render(
    <SidebarProvider>
      <DashboardSidebar />
    </SidebarProvider>
  );
};

describe('DashboardSidebar', () => {
  it.each([
    'Workflows',
    'Active',
    'Completed',
    'Failed',
    'Activity',
    'Settings',
  ])('renders %s menu item', (menuItem) => {
    renderSidebar();
    expect(screen.getByText(menuItem)).toBeInTheDocument();
  });

  it('renders branding and version info', () => {
    renderSidebar();
    expect(screen.getByText('AMELIA')).toBeInTheDocument();
    expect(screen.getByText(/Amelia/)).toBeInTheDocument();
  });
});
