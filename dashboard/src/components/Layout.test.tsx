import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Layout } from './Layout';

// Mock the hooks
const mockUseWebSocket = vi.fn();
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => mockUseWebSocket(),
}));

let mockIsConnected = true;
vi.mock('@/store/workflowStore', () => ({
  useWorkflowStore: vi.fn((selector) => {
    const state = { isConnected: mockIsConnected };
    return typeof selector === 'function' ? selector(state) : state;
  }),
}));

// Mock react-router-dom hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLocation: () => ({ pathname: '/workflows' }),
    useNavigation: () => ({ state: 'idle' }),
    Outlet: () => null,
    Link: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

describe('Layout WebSocket Initialization', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsConnected = true;
  });

  it('should initialize WebSocket on mount', () => {
    render(<Layout />);
    expect(mockUseWebSocket).toHaveBeenCalledTimes(1);
  });

  it('should display "Connected" when WebSocket is connected', () => {
    mockIsConnected = true;
    render(<Layout />);
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('should display "Disconnected" when WebSocket is disconnected', () => {
    mockIsConnected = false;
    render(<Layout />);
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });
});
