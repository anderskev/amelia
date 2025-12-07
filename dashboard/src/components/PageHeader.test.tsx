import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PageHeader } from './PageHeader';

describe('PageHeader', () => {
  describe('slot rendering', () => {
    it('renders all three slots when provided', () => {
      render(
        <PageHeader>
          <PageHeader.Left>Left content</PageHeader.Left>
          <PageHeader.Center>Center content</PageHeader.Center>
          <PageHeader.Right>Right content</PageHeader.Right>
        </PageHeader>
      );

      expect(screen.getByText('Left content')).toBeInTheDocument();
      expect(screen.getByText('Center content')).toBeInTheDocument();
      expect(screen.getByText('Right content')).toBeInTheDocument();
    });

    it('renders only left and center when right is omitted', () => {
      render(
        <PageHeader>
          <PageHeader.Left>Left content</PageHeader.Left>
          <PageHeader.Center>Center content</PageHeader.Center>
        </PageHeader>
      );

      expect(screen.getByText('Left content')).toBeInTheDocument();
      expect(screen.getByText('Center content')).toBeInTheDocument();
    });

    it('renders only left when center and right are omitted', () => {
      render(
        <PageHeader>
          <PageHeader.Left>Left only</PageHeader.Left>
        </PageHeader>
      );

      expect(screen.getByText('Left only')).toBeInTheDocument();
    });
  });

  describe('semantic structure', () => {
    it('has banner role', () => {
      render(
        <PageHeader>
          <PageHeader.Left>Content</PageHeader.Left>
        </PageHeader>
      );

      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('has data-slot attribute', () => {
      const { container } = render(
        <PageHeader>
          <PageHeader.Left>Content</PageHeader.Left>
        </PageHeader>
      );

      expect(container.querySelector('[data-slot="page-header"]')).toBeInTheDocument();
    });
  });

  describe('typography helpers', () => {
    it('renders Label with correct styling', () => {
      render(
        <PageHeader>
          <PageHeader.Left>
            <PageHeader.Label>WORKFLOW</PageHeader.Label>
          </PageHeader.Left>
        </PageHeader>
      );

      const label = screen.getByText('WORKFLOW');
      expect(label).toBeInTheDocument();
      expect(label).toHaveClass('text-xs', 'font-semibold', 'tracking-widest');
    });

    it('renders Title as h2', () => {
      render(
        <PageHeader>
          <PageHeader.Left>
            <PageHeader.Title>ISSUE-123</PageHeader.Title>
          </PageHeader.Left>
        </PageHeader>
      );

      const title = screen.getByRole('heading', { level: 2 });
      expect(title).toHaveTextContent('ISSUE-123');
      expect(title).toHaveClass('text-3xl', 'font-bold');
    });

    it('renders Subtitle with mono font', () => {
      render(
        <PageHeader>
          <PageHeader.Left>
            <PageHeader.Subtitle>feature-branch</PageHeader.Subtitle>
          </PageHeader.Left>
        </PageHeader>
      );

      const subtitle = screen.getByText('feature-branch');
      expect(subtitle).toHaveClass('font-mono', 'text-sm');
    });

    it('renders Value with primary color', () => {
      render(
        <PageHeader>
          <PageHeader.Center>
            <PageHeader.Value>02:34</PageHeader.Value>
          </PageHeader.Center>
        </PageHeader>
      );

      const value = screen.getByText('02:34');
      expect(value).toHaveClass('font-mono', 'text-2xl', 'text-primary');
    });

    it('applies glow effect when glow prop is true', () => {
      render(
        <PageHeader>
          <PageHeader.Center>
            <PageHeader.Value glow>02:34</PageHeader.Value>
          </PageHeader.Center>
        </PageHeader>
      );

      const value = screen.getByText('02:34');
      expect(value.className).toContain('text-shadow');
    });
  });

  describe('grid layout', () => {
    it('uses 3-column grid with equal outer columns when all slots present', () => {
      const { container } = render(
        <PageHeader>
          <PageHeader.Left>Left</PageHeader.Left>
          <PageHeader.Center>Center</PageHeader.Center>
          <PageHeader.Right>Right</PageHeader.Right>
        </PageHeader>
      );

      const header = container.querySelector('[data-slot="page-header"]');
      // Equal outer columns (1fr) ensure center is truly centered
      expect(header).toHaveClass('grid-cols-[1fr_auto_1fr]');
    });

    it('uses 3-column grid for true centering when only left and center', () => {
      const { container } = render(
        <PageHeader>
          <PageHeader.Left>Left</PageHeader.Left>
          <PageHeader.Center>Center</PageHeader.Center>
        </PageHeader>
      );

      const header = container.querySelector('[data-slot="page-header"]');
      // 3-column layout maintains true centering even without right slot
      expect(header).toHaveClass('grid-cols-[1fr_auto_1fr]');
    });

    it('uses single column when only left', () => {
      const { container } = render(
        <PageHeader>
          <PageHeader.Left>Left</PageHeader.Left>
        </PageHeader>
      );

      const header = container.querySelector('[data-slot="page-header"]');
      expect(header).toHaveClass('grid-cols-1');
    });
  });

  describe('className prop', () => {
    it('accepts custom className on PageHeader', () => {
      const { container } = render(
        <PageHeader className="custom-class">
          <PageHeader.Left>Content</PageHeader.Left>
        </PageHeader>
      );

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('accepts custom className on slots', () => {
      render(
        <PageHeader>
          <PageHeader.Left className="left-custom">Left</PageHeader.Left>
          <PageHeader.Center className="center-custom">Center</PageHeader.Center>
          <PageHeader.Right className="right-custom">Right</PageHeader.Right>
        </PageHeader>
      );

      expect(document.querySelector('.left-custom')).toBeInTheDocument();
      expect(document.querySelector('.center-custom')).toBeInTheDocument();
      expect(document.querySelector('.right-custom')).toBeInTheDocument();
    });
  });
});
