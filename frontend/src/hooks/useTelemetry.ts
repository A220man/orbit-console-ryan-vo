/** React Query hooks for telemetry */

import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { TelemetryMetric, ActorTelemetry, MetricsSummary } from '../types';

export const telemetryKeys = {
  all: ['telemetry'] as const,
  metrics: (params: Record<string, unknown>) => [...telemetryKeys.all, 'metrics', params] as const,
  actorTelemetry: (actorId: number, params: Record<string, unknown>) =>
    [...telemetryKeys.all, 'actor', actorId, params] as const,
  actorTelemetryByUid: (actorUid: string, params: Record<string, unknown>) =>
    [...telemetryKeys.all, 'actor', 'uid', actorUid, params] as const,
  statusGauge: (templateNamespace?: string, templateName?: string) =>
    [...telemetryKeys.all, 'status-gauge', templateNamespace, templateName] as const,
  crashCount: (templateNamespace?: string, templateName?: string) =>
    [...telemetryKeys.all, 'crash-count', templateNamespace, templateName] as const,
  summary: (sinceHours?: number) => [...telemetryKeys.all, 'summary', sinceHours] as const,
  ateActors: (templateNamespace?: string, templateName?: string) =>
    [...telemetryKeys.all, 'ate-actors', templateNamespace, templateName] as const,
  ateActorCrashes: (templateNamespace?: string, templateName?: string) =>
    [...telemetryKeys.all, 'ate-actor-crashes', templateNamespace, templateName] as const,
};

export function useMetrics(params?: {
  template_namespace?: string;
  template_name?: string;
  metric_name?: string;
  since_hours?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: telemetryKeys.metrics(params ?? {}),
    queryFn: () => api.getMetrics(params),
    staleTime: 15_000,
  });
}

export function useActorTelemetry(actorId: number, params?: {
  signal_type?: 'trace' | 'log';
  trace_id?: string;
  since_hours?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: telemetryKeys.actorTelemetry(actorId, params ?? {}),
    queryFn: () => api.getActorTelemetry(actorId, params),
    enabled: !!actorId,
    staleTime: 10_000,
  });
}

export function useActorTelemetryByUid(actorUid: string, params?: {
  signal_type?: 'trace' | 'log';
  trace_id?: string;
  since_hours?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: telemetryKeys.actorTelemetryByUid(actorUid, params ?? {}),
    queryFn: () => api.getActorTelemetryByUid(actorUid, params),
    enabled: !!actorUid,
    staleTime: 10_000,
  });
}

export function useStatusGauge(templateNamespace?: string, templateName?: string) {
  return useQuery({
    queryKey: telemetryKeys.statusGauge(templateNamespace, templateName),
    queryFn: () => api.getStatusGauge(templateNamespace, templateName),
    staleTime: 10_000,
  });
}

export function useCrashCount(templateNamespace?: string, templateName?: string) {
  return useQuery({
    queryKey: telemetryKeys.crashCount(templateNamespace, templateName),
    queryFn: () => api.getCrashCount(templateNamespace, templateName),
    staleTime: 10_000,
  });
}

export function useMetricsSummary(sinceHours?: number) {
  return useQuery({
    queryKey: telemetryKeys.summary(sinceHours),
    queryFn: () => api.getMetricsSummary(sinceHours),
    staleTime: 30_000,
  });
}

export function useAteActorsMetric(templateNamespace?: string, templateName?: string) {
  return useQuery({
    queryKey: telemetryKeys.ateActors(templateNamespace, templateName),
    queryFn: () => api.getAteActorsMetric(templateNamespace, templateName),
    staleTime: 10_000,
  });
}

export function useAteActorCrashesMetric(templateNamespace?: string, templateName?: string) {
  return useQuery({
    queryKey: telemetryKeys.ateActorCrashes(templateNamespace, templateName),
    queryFn: () => api.getAteActorCrashesMetric(templateNamespace, templateName),
    staleTime: 10_000,
  });
}