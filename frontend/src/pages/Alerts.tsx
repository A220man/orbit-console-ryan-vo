/** Alerts page */

import { useState } from 'react';
import { AlertTriangle, Bell, CheckCircle, XCircle, Filter, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button, Table } from '../ui';
import { cn } from '../../lib/utils';

interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  actor_uid?: string;
  template?: string;
  acknowledged: boolean;
  created_at: string;
}

const MOCK_ALERTS: Alert[] = [
  {
    id: '1',
    severity: 'critical',
    title: 'Actor Crashed',
    message: 'Actor worker-001 crashed due to OOM',
    actor_uid: 'worker-001',
    template: 'default/worker-v1',
    acknowledged: false,
    created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  },
  {
    id: '2',
    severity: 'warning',
    title: 'High Memory Usage',
    message: 'Actor worker-002 memory usage > 90%',
    actor_uid: 'worker-002',
    template: 'default/worker-v1',
    acknowledged: false,
    created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
  },
  {
    id: '3',
    severity: 'info',
    title: 'Actor Paused',
    message: 'Actor worker-003 paused by operator',
    actor_uid: 'worker-003',
    template: 'default/worker-v2',
    acknowledged: true,
    created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    id: '4',
    severity: 'critical',
    title: 'Node Unreachable',
    message: 'Node node-5 unreachable for 5 minutes',
    template: 'default/worker-v1',
    acknowledged: false,
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
];

export function Alerts() {
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'critical' | 'warning' | 'info'>('ALL');
  const [showAcknowledged, setShowAcknowledged] = useState(false);

  const filteredAlerts = MOCK_ALERTS.filter((alert) => {
    if (severityFilter !== 'ALL' && alert.severity !== severityFilter) return false;
    if (!showAcknowledged && alert.acknowledged) return false;
    return true;
  });

  const columns = [
    {
      key: 'severity',
      header: 'Severity',
      render: (alert: Alert) => (
        <Badge
          variant={
            alert.severity === 'critical' ? 'danger' :
            alert.severity === 'warning' ? 'warning' : 'info'
          }
        >
          {alert.severity.charAt(0).toUpperCase() + alert.severity.slice(1)}
        </Badge>
      ),
    },
    {
      key: 'title',
      header: 'Alert',
      render: (alert: Alert) => (
        <div>
          <div className="font-medium text-slate-900">{alert.title}</div>
          <div className="text-sm text-slate-500">{alert.message}</div>
        </div>
      ),
    },
    {
      key: 'actor',
      header: 'Actor / Template',
      render: (alert: Alert) => (
        <div className="text-sm text-slate-600 font-mono">
          {alert.actor_uid || '—'} / {alert.template || '—'}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (alert: Alert) => (
        <Badge variant={alert.acknowledged ? 'success' : 'warning'}>
          {alert.acknowledged ? 'Acknowledged' : 'Active'}
        </Badge>
      ),
    },
    {
      key: 'time',
      header: 'Time',
      render: (alert: Alert) => (
        <span className="text-sm text-slate-500">{new Date(alert.created_at).toLocaleString()}</span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (alert: Alert) => (
        <div className="flex items-center gap-1 justify-end">
          {!alert.acknowledged && (
            <Button variant="outline" size="sm" className="h-8 px-2" onClick={() => {}}>
              Acknowledge
            </Button>
          )}
          <Button variant="ghost" size="sm" className="h-8 px-2">
            Details
          </Button>
        </div>
      ),
    },
  ];

  const criticalCount = MOCK_ALERTS.filter(a => a.severity === 'critical' && !a.acknowledged).length;
  const warningCount = MOCK_ALERTS.filter(a => a.severity === 'warning' && !a.acknowledged).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Bell className="w-6 h-6" />
            Alerts
          </h1>
          <p className="text-slate-500 mt-1">System alerts and notifications</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={criticalCount > 0 ? 'danger' : 'success'} className="text-lg px-3 py-1">
            {criticalCount} Critical
          </Badge>
          <Badge variant={warningCount > 0 ? 'warning' : 'success'} className="text-lg px-3 py-1">
            {warningCount} Warning
          </Badge>
          <Button variant="outline" onClick={() => {}}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value as typeof severityFilter)}
                className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="ALL">All Severities</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={showAcknowledged}
                onChange={(e) => setShowAcknowledged(e.target.checked)}
                className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              Show acknowledged
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Alerts table */}
      <Card>
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={filteredAlerts}
            keyExtractor={(alert) => alert.id}
            emptyMessage="No alerts match current filters"
          />
        </CardContent>
      </Card>

      {/* Alert details (placeholder) */}
      <Card>
        <CardHeader>
          <CardTitle>Alert Details</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-500 text-center py-8">Select an alert to view details</p>
        </CardContent>
      </Card>
    </div>
  );
}