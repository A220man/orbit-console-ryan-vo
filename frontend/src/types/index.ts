/** Type definitions for API responses and domain models */

export type ActorStatus = 'RUNNING' | 'PAUSED' | 'SUSPENDED' | 'CRASHED';
export type SnapshotScope = 'full' | 'data';
export type SnapshotType = 'pause' | 'commit' | 'revert' | 'dump';

export interface Actor {
  id: number;
  uid: string;
  name: string;
  atespace: string;
  template_namespace: string;
  template_name: string;
  container_name: string;
  status: ActorStatus;
  snapshot_scope: SnapshotScope;
  node_id: string | null;
  worker_id: string | null;
  labels: Record<string, string>;
  annotations: Record<string, string>;
  created_at: string;
  updated_at: string;
  last_transition_at: string;
  resumed_at: string | null;
  paused_at: string | null;
  suspended_at: string | null;
  crashed_at: string | null;
}

export interface ActorListResponse {
  actors: Actor[];
  total: number;
  skip: number;
  limit: number;
}

export interface ActorCreate {
  uid: string;
  name: string;
  atespace: string;
  template_namespace: string;
  template_name: string;
  container_name?: string;
  snapshot_scope?: SnapshotScope;
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
}

export interface ActorUpdate {
  name?: string;
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
  snapshot_scope?: SnapshotScope;
}

export interface Snapshot {
  id: number;
  actor_id: number;
  actor_uid: string;
  snapshot_type: SnapshotType;
  scope: string;
  tag: string | null;
  storage_path: string;
  size_bytes: number;
  checksum: string | null;
  oci_image_digest: string | null;
  gvisor_version: string | null;
  metadata: Record<string, unknown>;
  is_valid: boolean;
  validation_error: string | null;
  created_at: string;
  expires_at: string | null;
}

export interface TelemetryMetric {
  id: number;
  template_namespace: string;
  template_name: string;
  container_name: string;
  metric_name: string;
  metric_type: 'counter' | 'gauge' | 'histogram';
  value: number;
  sum_value: number;
  count: number;
  min_value: number | null;
  max_value: number | null;
  labels: Record<string, string>;
  window_start: string;
  window_end: string;
  created_at: string;
}

export interface ActorTelemetry {
  id: number;
  actor_id: number;
  actor_uid: string;
  actor_name: string;
  atespace: string;
  signal_type: 'trace' | 'log';
  trace_id: string | null;
  span_id: string | null;
  parent_span_id: string | null;
  log_level: string | null;
  log_message: string | null;
  attributes: Record<string, unknown>;
  timestamp: string;
}

export interface MetricsSummary {
  actor_status_gauge: Array<{
    metric: string;
    status: string;
    template_namespace: string;
    template_name: string;
    value: number;
  }>;
  crash_count: number;
  transitions: Array<{
    template: string;
    from: string;
    to: string;
    count: number;
  }>;
  created_count: number;
  window_start: string;
  window_end: string;
}

export interface UserInfo {
  sub: string;
  email: string;
  name: string | null;
  roles: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface OIDCConfig {
  issuer: string;
  client_id: string;
  redirect_uri: string;
  scopes: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version?: string;
  database?: string;
  error?: string;
}