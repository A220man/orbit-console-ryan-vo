/** Hook tests */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import { useActors } from '../hooks/useActors';
import { useTelemetry } from '../hooks/useTelemetry';
import { api } from '../api/client';

// Mock API
vi.mock('../api/client', () => ({
  api: {
    getToken: vi.fn(),
    getOIDCConfig: vi.fn(),
    getCurrentUser: vi.fn(),
    listActors: vi.fn(),
    getActor: vi.fn(),
    createActor: vi.fn(),
    updateActor: vi.fn(),
    deleteActor: vi.fn(),
    pauseActor: vi.fn(),
    resumeActor: vi.fn(),
    commitActor: vi.fn(),
    revertActor: vi.fn(),
    dumpActor: vi.fn(),
    getActorStats: vi.fn(),
    getActorSnapshots: vi.fn(),
    getMetrics: vi.fn(),
    getActorTelemetry: vi.fn(),
    getStatusGauge: vi.fn(),
    getCrashCount: vi.fn(),
    getMetricsSummary: vi.fn(),
    getAteActorsMetric: vi.fn(),
    getAteActorCrashesMetric: vi.fn(),
    logout: vi.fn(),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('returns unauthenticated state initially', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(true);
  });
});

describe('useActors', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches actors list', async () => {
    const mockActors = {
      actors: [
        { id: 1, uid: 'actor-1', name: 'Actor 1', status: 'RUNNING' as const },
        { id: 2, uid: 'actor-2', name: 'Actor 2', status: 'SUSPENDED' as const },
      ],
      total: 2,
      skip: 0,
      limit: 100,
    };

    api.listActors.mockResolvedValue(mockActors);

    const { result } = renderHook(() => useActors(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockActors);
  });
});

describe('useTelemetry', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches status gauge', async () => {
    const mockGauge = [
      { metric: 'ate_actors', status: 'running', template_namespace: '*', template_name: '*', value: 5 },
      { metric: 'ate_actors', status: 'paused', template_namespace: '*', template_name: '*', value: 2 },
      { metric: 'ate_actors', status: 'suspended', template_namespace: '*', template_name: '*', value: 10 },
      { metric: 'ate_actors', status: 'crashed', template_namespace: '*', template_name: '*', value: 1 },
    ];

    api.getStatusGauge.mockResolvedValue(mockGauge);

    const { result } = renderHook(() => useStatusGauge(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockGauge);
  });

  it('fetches crash count', async () => {
    api.getCrashCount.mockResolvedValue({ crash_count: 3 });

    const { result } = renderHook(() => useCrashCount(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ crash_count: 3 });
  });
});