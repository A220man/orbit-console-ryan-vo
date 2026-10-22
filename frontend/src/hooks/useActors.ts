/** React Query hooks for actor management */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { Actor, ActorListResponse, ActorCreate, ActorUpdate, Snapshot, ActorStatus, SnapshotScope } from '../types';

// Query keys
export const actorKeys = {
  all: ['actors'] as const,
  lists: () => [...actorKeys.all, 'list'] as const,
  list: (params: Record<string, unknown>) => [...actorKeys.lists(), params] as const,
  details: () => [...actorKeys.all, 'detail'] as const,
  detail: (id: number) => [...actorKeys.details(), id] as const,
  byUid: (uid: string) => [...actorKeys.details(), 'uid', uid] as const,
  stats: () => [...actorKeys.all, 'stats'] as const,
  snapshots: (actorId: number) => [...actorKeys.all, 'snapshots', actorId] as const,
};

export function useActors(params?: {
  skip?: number;
  limit?: number;
  status?: ActorStatus;
  atespace?: string;
  template_namespace?: string;
  template_name?: string;
  node_id?: string;
}) {
  return useQuery({
    queryKey: actorKeys.list(params ?? {}),
    queryFn: () => api.listActors(params),
    staleTime: 10_000,
  });
}

export function useActor(id: number) {
  return useQuery({
    queryKey: actorKeys.detail(id),
    queryFn: () => api.getActor(id),
    enabled: !!id,
  });
}

export function useActorByUid(uid: string) {
  return useQuery({
    queryKey: actorKeys.byUid(uid),
    queryFn: () => api.getActorByUid(uid),
    enabled: !!uid,
  });
}

export function useActorStats() {
  return useQuery({
    queryKey: actorKeys.stats(),
    queryFn: () => api.getActorStats(),
    staleTime: 30_000,
  });
}

export function useActorSnapshots(actorId: number, params?: { snapshot_type?: string; tag?: string }) {
  return useQuery({
    queryKey: actorKeys.snapshots(actorId),
    queryFn: () => api.getActorSnapshots(actorId, params),
    enabled: !!actorId,
  });
}

export function useCreateActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ActorCreate) => api.createActor(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.stats() });
    },
  });
}

export function useUpdateActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ActorUpdate }) => api.updateActor(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.detail(id) });
    },
  });
}

export function useDeleteActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteActor(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.stats() });
    },
  });
}

export function usePauseActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, timerSeconds, snapshotScope }: { id: number; timerSeconds?: number; snapshotScope?: SnapshotScope }) =>
      api.pauseActor(id, timerSeconds, snapshotScope),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: actorKeys.snapshots(id) });
    },
  });
}

export function useResumeActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, nodeId, workerId }: { id: number; nodeId?: string; workerId?: string }) =>
      api.resumeActor(id, nodeId, workerId),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.detail(id) });
    },
  });
}

export function useCommitActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, tag, snapshotScope }: { id: number; tag?: string; snapshotScope?: SnapshotScope }) =>
      api.commitActor(id, tag, snapshotScope),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: actorKeys.snapshots(id) });
    },
  });
}

export function useRevertActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, tag, snapshotId }: { id: number; tag?: string; snapshotId?: number }) =>
      api.revertActor(id, tag, snapshotId),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: actorKeys.snapshots(id) });
    },
  });
}

export function useDumpActor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, tag }: { id: number; tag: string }) => api.dumpActor(id, tag),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: actorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: actorKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: actorKeys.snapshots(id) });
    },
  });
}