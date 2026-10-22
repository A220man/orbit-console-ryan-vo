/** Dashboard page */

import { useQuery } from '@tanstack/react-query';
import { Server, AlertTriangle, Plus, RefreshCw, TrendingUp } from 'lucide-react';
import { api } from '../../api/client';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '../ui';
import { cn, formatRelativeTime, getStatusColor, getStatusIcon } from '../../lib/utils';
import { useActors } from '../../hooks';
import { ActorStatus } from '../../types';

export function Dashboard() {
  const { data: actorsResponse } = useActors({ limit: 10 });
  const { data: stats } = useQuery({
    queryKey: ['actors', 'stats'],
    queryFn: () => api.getActorStats(),
    staleTime: 30_000,
  });

  const actors = actorsResponse?.actors ?? [];
  const total = actorsResponse?.total ?? 0;

  // Status counts
  const statusCounts = {
    RUNNING: actors.filter((a) => a.status === 'RUNNING').length,
    PAUSED: actors.filter((a) => a.status === 'PAUSED').length,
    SUSPENDED: actors.filter((a) => a.status === 'SUSPENDED').length,
    CRASHED: actors.filter((a) => a.status === 'CRASHED').length,
  };

  const statusCards = [
    { label: 'Running', count: statusCounts.RUNNING, icon: Server, color: 'text-green-600 bg-green-100', status: 'RUNNING' as ActorStatus },
    { label: 'Paused', count: statusCounts.PAUSED, icon: AlertTriangle, color: 'text-yellow-600 bg-yellow-100', status: 'PAUSED' as ActorStatus },
    { label: 'Suspended', count: statusCounts.SUSPENDED, icon: Server, color: 'text-blue-600 bg-blue-100', status: 'SUSPENDED' as ActorStatus },
    { label: 'Crashed', count: statusCounts.CRASHED, icon: AlertTriangle, color: 'text-red-600 bg-red-100', status: 'CRASHED' as ActorStatus },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 mt-1">Actor lifecycle overview</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Actor
        </Button>
      </div>

      {/* Status cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statusCards.map(({ label, count, icon: Icon, color, status }) => (
          <Card key={label}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">{label}</p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">{count}</p>
                </div>
                <div className={cn('p-3 rounded-xl', color)}>
                  <Icon className="w-6 h-6" aria-hidden="true" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent actors */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Actors</CardTitle>
          <Button variant="ghost" size="sm" onClick={() => {}}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {actors.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Server className="w-12 h-12 mx-auto text-slate-300 mb-3" />
              <p>No actors found</p>
              <p className="text-sm">Create your first actor to get started</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Actor</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Atespace</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Template</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Updated</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {actors.map((actor) => (
                    <tr key={actor.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">{actor.name}</div>
                        <div className="text-sm text-slate-500">{actor.uid}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{actor.atespace}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {actor.template_namespace}/{actor.template_name}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={actor.status === 'RUNNING' ? 'success' : actor.status === 'CRASHED' ? 'danger' : actor.status === 'PAUSED' ? 'warning' : 'info'}>
                          {getStatusIcon(actor.status)} {actor.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-500">{formatRelativeTime(actor.updated_at)}</td>
                      <td className="px-4 py-3 text-right">
                        <Button variant="ghost" size="sm" className="text-slate-600 hover:text-primary-600">
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Actors</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{total}</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-100 text-purple-600">
                <TrendingUp className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Templates</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">
                  {new Set(actors.map(a => `${a.template_namespace}/${a.template_name}`)).size}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-orange-100 text-orange-600">
                <Server className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Atespaces</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">
                  {new Set(actors.map(a => a.atespace)).size}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-cyan-100 text-cyan-600">
                <Activity className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}