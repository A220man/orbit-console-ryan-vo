/** Component tests */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardContent } from '../components/ui/Card';
import { Modal, ConfirmDialog } from '../components/ui/Modal';
import { cn } from '../lib/utils';

// Test wrapper
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {ui}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('cn utility', () => {
  it('merges class names correctly', () => {
    expect(cn('base', 'extra')).toBe('base extra');
    expect(cn('base', false && 'conditional')).toBe('base');
    expect(cn('base', { conditional: true })).toBe('base conditional');
    expect(cn('base', { conditional: false })).toBe('base');
  });
});

describe('Button', () => {
  it('renders children', () => {
    renderWithProviders(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderWithProviders(<Button loading>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeDisabled();
    expect(screen.getByRole('button')).toContainHTML('svg');
  });

  it('applies variant classes', () => {
    renderWithProviders(<Button variant="danger">Delete</Button>);
    const button = screen.getByRole('button', { name: 'Delete' });
    expect(button).toHaveClass('bg-red-600');
  });

  it('applies size classes', () => {
    renderWithProviders(<Button size="lg">Large</Button>);
    const button = screen.getByRole('button', { name: 'Large' });
    expect(button).toHaveClass('px-6', 'py-3', 'text-base');
  });
});

describe('Badge', () => {
  it('renders with default variant', () => {
    renderWithProviders(<Badge>Default</Badge>);
    expect(screen.getByText('Default')).toHaveClass('bg-slate-100', 'text-slate-700');
  });

  it('applies variant classes', () => {
    renderWithProviders(<Badge variant="success">Success</Badge>);
    expect(screen.getByText('Success')).toHaveClass('bg-green-100', 'text-green-700');
  });

  it('applies size classes', () => {
    renderWithProviders(<Badge size="sm">Small</Badge>);
    expect(screen.getByText('Small')).toHaveClass('px-2', 'py-0.5', 'text-xs');
  });
});

describe('Card', () => {
  it('renders children', () => {
    renderWithProviders(
      <Card>
        <CardContent>Card content</CardContent>
      </Card>
    );
    expect(screen.getByText('Card content')).toBeInTheDocument();
    expect(screen.getByText('Card content').closest('div')).toHaveClass('bg-white', 'rounded-xl');
  });
});

describe('Modal', () => {
  it('renders when open', () => {
    renderWithProviders(
      <Modal isOpen={true} onClose={() => {}} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    renderWithProviders(
      <Modal isOpen={false} onClose={() => {}} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('closes on backdrop click', () => {
    const onClose = vi.fn();
    renderWithProviders(
      <Modal isOpen={true} onClose={onClose} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    fireEvent.click(screen.getByTestId('modal-backdrop') ?? screen.getByRole('dialog').parentElement!);
    expect(onClose).toHaveBeenCalled();
  });
});

describe('ConfirmDialog', () => {
  it('renders with confirm and cancel buttons', () => {
    renderWithProviders(
      <ConfirmDialog
        isOpen={true}
        onClose={() => {}}
        onConfirm={() => {}}
        title="Confirm"
        message="Are you sure?"
      />
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
  });

  it('calls onConfirm when confirm clicked', () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    renderWithProviders(
      <ConfirmDialog
        isOpen={true}
        onClose={onClose}
        onConfirm={onConfirm}
        title="Confirm"
        message="Are you sure?"
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(onConfirm).toHaveBeenCalled();
  });
});

describe('useAuth hook', () => {
  it('provides auth context', () => {
    function TestComponent() {
      const { user, isLoading, isAuthenticated, login, logout, checkAuth } = useAuth();
      return (
        <div>
          <span data-testid="user">{user?.email || 'none'}</span>
          <span data-testid="loading">{String(isLoading)}</span>
          <span data-testid="authenticated">{String(isAuthenticated)}</span>
        </div>
      );
    }

    renderWithProviders(<TestComponent />);
    expect(screen.getByTestId('user')).toHaveTextContent('none');
    expect(screen.getByTestId('loading')).toHaveTextContent('true');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
  });
});