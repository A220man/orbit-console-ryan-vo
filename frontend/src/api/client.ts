/** Typed API client generated from backend routes */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  Actor,
  ActorListResponse,
  ActorCreate,
  ActorUpdate,
  Snapshot,
  TelemetryMetric,
  ActorTelemetry,
  MetricsSummary,
  UserInfo,
  TokenResponse,
  OIDCConfig,
  HealthResponse,
  ActorStatus,
  SnapshotScope,
  SnapshotType,
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30_000,
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearToken();
          // Redirect to login if not already there
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.accessToken = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = localStorage.getItem('access_token');
    }
    return this.accessToken;
  }

  clearToken() {
    this.accessToken = null;
    localStorage.removeItem('access_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // Health
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async readiness(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health/ready');
    return response.data;
  }

  // Auth
  async getOIDCConfig(): Promise<OIDCConfig> {
    const response = await this.client.get<OIDCConfig>('/auth/config');
    return response.data;
  }

  async getCurrentUser(): Promise<UserInfo> {
    const response = await this.client.get<UserInfo>('/auth/me');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
    this.clearToken();
  }

  // Actors
  async listActors(params?: {
    skip?: number;
    limit?: number;
    status?: ActorStatus;
    atespace?: string;
    template_namespace?: string;
    template_name?: string;
    node_id?: string;
  }): Promise<ActorListResponse> {
    const response = await this.client.get<ActorListResponse>('/actors', { params });
    return response.data;
  }

  async getActor(id: number): Promise<Actor> {
    const response = await this.client.get<Actor>(`/actors/${id}`);
    return response.data;
  }

  async getActorByUid(uid: string): Promise<Actor> {
    const response = await this.client.get<Actor>(`/actors/uid/${uid}`);
    return response.data;
  }

  async createActor(data: ActorCreate): Promise<Actor> {
    const response = await this.client.post<Actor>('/actors', data);
    return response.data;
  }

  async updateActor(id: number, data: ActorUpdate): Promise<Actor> {
    const response = await this.client.patch<Actor>(`/actors/${id}`, data);
    return response.data;
  }

  async deleteActor(id: number): Promise<void> {
    await this.client.delete(`/actors/${id}`);
  }

  async pauseActor(id: number, timerSeconds?: number, snapshotScope?: SnapshotScope): Promise<Actor> {
    const response = await this.client.post<Actor>(`/actors/${id}/pause`, {
      timer_seconds: timerSeconds,
      snapshot_scope: snapshotScope,
    });
    return response.data;
  }

  async resumeActor(id: number, nodeId?: string, workerId?: string): Promise<Actor> {
    const response = await this.client.post<Actor>(`/actors/${id}/resume`, null, {
      params: { node_id: nodeId, worker_id: workerId },
    });
    return response.data;
  }

  async commitActor(id: number, tag?: string, snapshotScope?: SnapshotScope): Promise<Actor> {
    const response = await this.client.post<Actor>(`/actors/${id}/commit`, {
      tag,
      snapshot_scope: snapshotScope,
    });
    return response.data;
  }

  async revertActor(id: number, tag?: string, snapshotId?: number): Promise<Actor> {
    const response = await this.client.post<Actor>(`/actors/${id}/revert`, {
      tag,
      snapshot_id: snapshotId,
    });
    return response.data;
  }

  async dumpActor(id: number, tag: string): Promise<Actor> {
    const response = await this.client.post<Actor>(`/actors/${id}/dump`, { tag });
    return response.data;
  }

  async getActorStats(): Promise<Record<string, unknown>> {
    const response = await this.client.get('/actors/stats');
    return response.data;
  }

  async getActorSnapshots(
    actorId: number,
    params?: { snapshot_type?: SnapshotType; tag?: string; skip?: number; limit?: number }
  ): Promise<Snapshot[]> {
    const response = await this.client.get<Snapshot[]>(`/actors/${actorId}/snapshots`, { params });
    return response.data;
  }

  // Snapshots
  async listSnapshots(params?: {
    actor_id?: number;
    actor_uid?: string;
    snapshot_type?: SnapshotType;
    tag?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ snapshots: Snapshot[]; total: number; skip: number; limit: number }> {
    const response = await this.client.get('/snapshots', { params });
    return response.data;
  }

  async getSnapshot(id: number): Promise<Snapshot> {
    const response = await this.client.get<Snapshot>(`/snapshots/${id}`);
    return response.data;
  }

  async validateSnapshot(id: number): Promise<{ snapshot_id: number; is_valid: boolean; error: string | null }> {
    const response = await this.client.post(`/snapshots/${id}/validate`);
    return response.data;
  }

  // Telemetry
  async getMetrics(params?: {
    template_namespace?: string;
    template_name?: string;
    metric_name?: string;
    since_hours?: number;
    limit?: number;
  }): Promise<TelemetryMetric[]> {
    const response = await this.client.get<TelemetryMetric[]>('/telemetry/metrics', { params });
    return response.data;
  }

  async getActorTelemetry(actorId: number, params?: {
    signal_type?: 'trace' | 'log';
    trace_id?: string;
    since_hours?: number;
    limit?: number;
  }): Promise<ActorTelemetry[]> {
    const response = await this.client.get<ActorTelemetry[]>(`/telemetry/actors/${actorId}/telemetry`, { params });
    return response.data;
  }

  async getActorTelemetryByUid(actorUid: string, params?: {
    signal_type?: 'trace' | 'log';
    trace_id?: string;
    since_hours?: number;
    limit?: number;
  }): Promise<ActorTelemetry[]> {
    const response = await this.client.get<ActorTelemetry[]>('/telemetry/actors/telemetry', {
      params: { actor_uid: actorUid, ...params },
    });
    return response.data;
  }

  async getStatusGauge(templateNamespace?: string, templateName?: string): Promise<Array<{
    metric: string;
    status: string;
    template_namespace: string;
    template_name: string;
    value: number;
  }>> {
    const response = await this.client.get('/telemetry/status-gauge', {
      params: { template_namespace: templateNamespace, template_name: templateName },
    });
    return response.data;
  }

  async getCrashCount(templateNamespace?: string, templateName?: string): Promise<{ crash_count: number }> {
    const response = await this.client.get('/telemetry/crash-count', {
      params: { template_namespace: templateNamespace, template_name: templateName },
    });
    return response.data;
  }

  async getMetricsSummary(sinceHours?: number): Promise<MetricsSummary> {
    const response = await this.client.get<MetricsSummary>('/telemetry/summary', {
      params: { since_hours: sinceHours },
    });
    return response.data;
  }

  async getAteActorsMetric(templateNamespace?: string, templateName?: string): Promise<{ metric: string; format: string; data: string }> {
    const response = await this.client.get('/telemetry/ate-actors', {
      params: { template_namespace: templateNamespace, template_name: templateName },
    });
    return response.data;
  }

  async getAteActorCrashesMetric(templateNamespace?: string, templateName?: string): Promise<{ metric: string; format: string; data: string }> {
    const response = await this.client.get('/telemetry/ate-actor-crashes', {
      params: { template_namespace: templateNamespace, template_name: templateName },
    });
    return response.data;
  }
}

export const api = new ApiClient();