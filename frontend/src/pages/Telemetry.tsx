/** Telemetry dashboard page */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Download, BarChart2, AlertTriangle, TrendingUp } from 'lucide-react';
import { api } from '../../api/client';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '../ui';
import { cn, formatRelativeTime } from '../../lib/utils';
import { useMetrics, useStatusGauge, useCrashCount, useMetricsSummary, useAteActorsMetric } from '../../hooks';
import { ActorTelemetry } from '../../types';

export function Telemetry() {
  const [timeRange, setTimeRange] = useState(1);
  const [templateNamespace, setTemplateNamespace] = useState('');
  const [templateName, setTemplateName] = useState('');

  const { data: summary } = useMetricsSummary(timeRange);
  const { data: statusGauge } = useStatusGauge(templateNamespace || undefined, templateName || undefined);
  const { data: crashCount } = useCrashCount(templateNamespace || undefined, templateName || undefined);
  const { data: metrics } = useMetrics({
    template_namespace: templateNamespace || undefined,
    template_name: templateName || undefined,
    since_hours: timeRange,
    limit: 100,
  });
  const { data: ateActorsMetric } = useAteActorsMetric(templateNamespace || undefined, templateName || undefined);

  const statusData = statusGauge || [];
  const runningCount = statusData.find(d => d.status === 'running')?.value || 0;
  const pausedCount = statusData.find(d => d.status === 'paused')?.value || 0;
  const suspendedCount = statusData.find(d => d.status === 'suspended')?.value || 0;
  const crashedCount = statusData.find(d => d.status === 'crashed')?.value || 0;

  const transitions = summary?.transitions || [];
  const createdCount = summary?.created_count || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Telemetry</h1>
          <p className="text-slate-500 mt-1">Actor metrics and monitoring</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
          </select>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" onClick={() => {}}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input
              placeholder="Template Namespace"
              value={templateNamespace}
              onChange={(e) => setTemplateNamespace(e.target.value)}
              className="max-w-md"
            />
            <Input
              placeholder="Template Name"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              className="max-w-md"
            />
          </div>
        </CardContent>
      </Card>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Running</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{runningCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-green-100 text-green-600">
                <TrendingUp className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Paused</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{pausedCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-yellow-100 text-yellow-600">
                <TrendingUp className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Suspended</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{suspendedCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-100 text-blue-600">
                <TrendingUp className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Crashed</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{crashedCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-red-100 text-red-600">
                <AlertTriangle className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Created (period)</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{createdCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-100 text-purple-600">
                <BarChart2 className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ate.actors gauge visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Actor Status Gauge (ate.actors)</CardTitle>
        </CardHeader>
        <CardContent>
          {ateActorsMetric ? (
            <div className="font-mono text-sm bg-slate-900 text-green-300 p-4 rounded-lg overflow-x-auto">
              <pre>{ateActorsMetric.data}</pre>
            </div>
          ) : (
            <div className="space-y-3">
              {statusData.map((d) => (
                <div key={d.status} className="flex items-center gap-4">
                  <Badge variant={
                    d.status === 'running' ? 'success' :
                    d.status === 'crashed' ? 'danger' :
                    d.status === 'paused' ? 'warning' : 'info'
                  } className="w-24 text-center capitalize">
                    {d.status}
                  </Badge>
                  <div className="flex-1 h-4 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all duration-500',
                        d.status === 'running' && 'bg-green-500',
                        d.status === 'paused' && 'bg-yellow-500',
                        d.status === 'suspended' && 'bg-blue-500',
                        d.status === 'crashed' && 'bg-red-500'
                      )}
                      style={{ width: `${Math.min((d.value / (runningCount + pausedCount + suspendedCount + crashedCount || 1)) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="w-16 text-right font-mono text-slate-600">{d.value}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Crash counter */}
      <Card>
        <CardHeader>
          <CardTitle>Crash Counter (ate.actor.crashes)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <AlertTriangle className="w-16 h-16 mx-auto text-red-500 mb-4" />
            <p className="text-4xl font-bold text-slate-900">{crashCount?.crash_count || 0}</p>
            <p className="text-slate-500 mt-1">Actors currently in CRASHED state</p>
          </div>
        </CardContent>
      </Card>

      {/* Recent transitions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent State Transitions</CardTitle>
        </CardHeader>
        <CardContent>
          {transitions.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No transitions in selected time range</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Template</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">From</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">To</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Count</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {transitions.map((t, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-3 text-sm text-slate-900 font-mono">{t.template}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 capitalize">{t.from}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 capitalize">{t.to}</td>
                      <td className="px-4 py-3 text-sm font-medium text-slate-900">{t.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Raw metrics table */}
      <Card>
        <CardHeader>
          <CardTitle>Raw Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          {metrics && metrics.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Template</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Metric</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Value</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Window</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {metrics.slice(0, 50).map((m, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-3 text-sm text-slate-600 font-mono">{m.template_namespace}/{m.template_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{m.metric_name}</td>
                      <td className="px-4 py-3 text-sm">
                        <Badge variant="default" className="capitalize">{m.metric_type}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-900">{m.value.toLocaleString()}</td>
                      <td className="px-4 py-3 text-sm text-slate-500">{formatRelativeTime(m.window_start)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-slate-500 text-center py-8">No metrics available</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

import { Input } from '../ui';