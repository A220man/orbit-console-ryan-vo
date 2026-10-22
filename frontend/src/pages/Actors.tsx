/** Actors list and management page */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Filter, ChevronDown, ChevronUp, RefreshCw, Play, Pause, Save, RotateCcw, HardDrive, Trash2, Eye } from 'lucide-react';
import { api } from '../../api/client';
import { Card, CardHeader, CardTitle, CardContent, CardFooter, Button, Badge, Input, Modal, Table } from '../ui';
import { cn, formatRelativeTime, getStatusIcon, getStatusColor } from '../../lib/utils';
import { useActors, useCreateActor, usePauseActor, useResumeActor, useCommitActor, useRevertActor, useDumpActor, useDeleteActor, useUpdateActor } from '../../hooks';
import { Actor, ActorStatus, SnapshotScope, ActorCreate, ActorUpdate } from '../../types';
import { useAuth } from '../../hooks';

const STATUSES: ActorStatus[] = ['RUNNING', 'PAUSED', 'SUSPENDED', 'CRASHED'];

export function Actors() {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ActorStatus | 'ALL'>('ALL');
  const [atespaceFilter, setAtespaceFilter] = useState('');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<ActorCreate>({
    uid: '',
    name: '',
    atespace: 'default',
    template_namespace: 'default',
    template_name: '',
    container_name: 'main',
    snapshot_scope: 'data',
  });

  const { data: actorsResponse, isLoading, refetch } = useActors({
    skip: page * pageSize,
    limit: pageSize,
    status: statusFilter === 'ALL' ? undefined : statusFilter,
    atespace: atespaceFilter || undefined,
  });

  const actors = actorsResponse?.actors ?? [];
  const total = actorsResponse?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  const createActorMutation = useCreateActor();
  const pauseActorMutation = usePauseActor();
  const resumeActorMutation = useResumeActor();
  const commitActorMutation = useCommitActor();
  const revertActorMutation = useRevertActor();
  const dumpActorMutation = useDumpActor();
  const deleteActorMutation = useDeleteActor();

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createActorMutation.mutateAsync(createForm);
      setShowCreateModal(false);
      setCreateForm({
        uid: '', name: '', atespace: 'default', template_namespace: 'default',
        template_name: '', container_name: 'main', snapshot_scope: 'data',
      });
      refetch();
    } catch (error) {
      console.error('Failed to create actor:', error);
    }
  };

  const handleAction = async (
    actor: Actor,
    action: 'pause' | 'resume' | 'commit' | 'revert' | 'dump' | 'delete',
    tag?: string
  ) => {
    try {
      switch (action) {
        case 'pause':
          await pauseActorMutation.mutateAsync({ id: actor.id, timerSeconds: 300 });
          break;
        case 'resume':
          await resumeActorMutation.mutateAsync({ id: actor.id });
          break;
        case 'commit':
          await commitActorMutation.mutateAsync({ id: actor.id, tag });
          break;
        case 'revert':
          await revertActorMutation.mutateAsync({ id: actor.id, tag });
          break;
        case 'dump':
          await dumpActorMutation.mutateAsync({ id: actor.id, tag: tag || `dump-${Date.now()}` });
          break;
        case 'delete':
          await deleteActorMutation.mutateAsync(actor.id);
          break;
      }
      refetch();
    } catch (error) {
      console.error(`Failed to ${action} actor:`, error);
    }
  };

  const getAvailableActions = (actor: Actor) => {
    const actions = [];
    if (actor.status === 'RUNNING') {
      actions.push({ label: 'Pause', action: 'pause' as const, icon: Pause, variant: 'secondary' });
      actions.push({ label: 'Commit', action: 'commit' as const, icon: Save, variant: 'primary' });
    }
    if (actor.status === 'PAUSED') {
      actions.push({ label: 'Resume', action: 'resume' as const, icon: Play, variant: 'success' });
      actions.push({ label: 'Commit', action: 'commit' as const, icon: Save, variant: 'primary' });
    }
    if (actor.status === 'SUSPENDED') {
      actions.push({ label: 'Resume', action: 'resume' as const, icon: Play, variant: 'success' });
      actions.push({ label: 'Revert', action: 'revert' as const, icon: RotateCcw, variant: 'secondary' });
    }
    if (actor.status === 'CRASHED') {
      actions.push({ label: 'Dump', action: 'dump' as const, icon: HardDrive, variant: 'warning' });
      actions.push({ label: 'Revert', action: 'revert' as const, icon: RotateCcw, variant: 'secondary' });
    }
    if (actor.status !== 'RUNNING') {
      actions.push({ label: 'Delete', action: 'delete' as const, icon: Trash2, variant: 'danger' });
    }
    return actions;
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Please log in to view actors</p>
      </div>
    );
  }

  const columns = [
    {
      key: 'name',
      header: 'Actor',
      render: (actor: Actor) => (
        <div>
          <div className="font-medium text-slate-900">{actor.name}</div>
          <div className="text-sm text-slate-500 font-mono">{actor.uid}</div>
        </div>
      ),
    },
    {
      key: 'atespace',
      header: 'Atespace',
      render: (actor: Actor) => <span className="text-sm text-slate-600">{actor.atespace}</span>,
    },
    {
      key: 'template',
      header: 'Template',
      render: (actor: Actor) => (
        <span className="text-sm text-slate-600">{actor.template_namespace}/{actor.template_name}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (actor: Actor) => (
        <Badge variant={actor.status === 'RUNNING' ? 'success' : actor.status === 'CRASHED' ? 'danger' : actor.status === 'PAUSED' ? 'warning' : 'info'}>
          {getStatusIcon(actor.status)} {actor.status}
        </Badge>
      ),
    },
    {
      key: 'updated',
      header: 'Updated',
      render: (actor: Actor) => <span className="text-sm text-slate-500">{formatRelativeTime(actor.updated_at)}</span>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (actor: Actor) => {
        const actions = getAvailableActions(actor);
        return (
          <div className="flex items-center gap-1 justify-end">
            {actions.map(({ label, action, icon: Icon, variant }) => (
              <Button
                key={action}
                variant={variant as any}
                size="sm"
                className="h-8 px-2"
                onClick={() => handleAction(actor, action, `manual-${Date.now()}`)}
                disabled={createActorMutation.isPending || pauseActorMutation.isPending || resumeActorMutation.isPending}
              >
                <Icon className="w-3.5 h-3.5" />
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Actors</h1>
          <p className="text-slate-500 mt-1">Manage actor lifecycles</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Actor
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search actors..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as ActorStatus | 'ALL')}
                className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="ALL">All Statuses</option>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <Input
                placeholder="Filter by atespace"
                value={atespaceFilter}
                onChange={(e) => setAtespaceFilter(e.target.value)}
                className="w-48"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actors table */}
      <Card>
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={actors}
            keyExtractor={(actor) => actor.id}
            loading={isLoading}
            emptyMessage="No actors found"
            onRowClick={(actor) => {}}
          />
        </CardContent>
        {total > 0 && (
          <CardFooter className="flex items-center justify-between px-4 py-3">
            <span className="text-sm text-slate-500">
              Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm text-slate-600">Page {page + 1} of {totalPages}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </CardFooter>
        )}
      </Card>

      {/* Create Actor Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Actor"
        description="Add a new actor to the system"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={handleCreate} loading={createActorMutation.isPending}>Create</Button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="UID"
              value={createForm.uid}
              onChange={(e) => setCreateForm({ ...createForm, uid: e.target.value })}
              placeholder="actor-001"
              required
            />
            <Input
              label="Name"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              placeholder="My Actor"
              required
            />
            <Input
              label="Atespace"
              value={createForm.atespace}
              onChange={(e) => setCreateForm({ ...createForm, atespace: e.target.value })}
              placeholder="default"
              required
            />
            <Input
              label="Template Namespace"
              value={createForm.template_namespace}
              onChange={(e) => setCreateForm({ ...createForm, template_namespace: e.target.value })}
              placeholder="default"
              required
            />
            <Input
              label="Template Name"
              value={createForm.template_name}
              onChange={(e) => setCreateForm({ ...createForm, template_name: e.target.value })}
              placeholder="worker-v1"
              required
            />
            <Input
              label="Container Name"
              value={createForm.container_name}
              onChange={(e) => setCreateForm({ ...createForm, container_name: e.target.value })}
              placeholder="main"
            />
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Snapshot Scope</label>
              <select
                value={createForm.snapshot_scope}
                onChange={(e) => setCreateForm({ ...createForm, snapshot_scope: e.target.value as SnapshotScope })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="data">Data (durabledir only)</option>
                <option value="full">Full (memory + filesystem)</option>
              </select>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
}

import { ChevronLeft, ChevronRight } from 'lucide-react';