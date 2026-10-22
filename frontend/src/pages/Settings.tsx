/** Settings page */

import { useState } from 'react';
import { User, Shield, Key, Database, Server, Save, Bell, Moon, Globe } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Badge } from '../ui';
import { useAuth } from '../../hooks';

export function Settings() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'notifications' | 'appearance'>('profile');
  const [settings, setSettings] = useState({
    email: user?.email || '',
    name: user?.name || '',
    timezone: 'UTC',
    language: 'en',
    emailNotifications: true,
    pushNotifications: false,
    alertThreshold: 'warning',
    theme: 'system' as 'light' | 'dark' | 'system',
    compactMode: false,
  });

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Moon },
  ];

  const handleSave = async () => {
    // In real app, call API to save settings
    console.log('Saving settings:', settings);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 mt-1">Manage your account and preferences</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar */}
        <Card className="lg:w-64 flex-shrink-0">
          <CardContent className="p-2">
            <nav className="space-y-1" role="navigation" aria-label="Settings sections">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="w-5 h-5" aria-hidden="true" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </CardContent>
        </Card>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle>Profile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input
                    label="Email"
                    value={settings.email}
                    onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                    type="email"
                    disabled
                  />
                  <Input
                    label="Name"
                    value={settings.name}
                    onChange={(e) => setSettings({ ...settings, name: e.target.value })}
                    placeholder="Your name"
                  />
                  <Input
                    label="Timezone"
                    value={settings.timezone}
                    onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                  />
                  <Input
                    label="Language"
                    value={settings.language}
                    onChange={(e) => setSettings({ ...settings, language: e.target.value })}
                  />
                </div>
                <div className="flex justify-end pt-4 border-t border-slate-200">
                  <Button onClick={handleSave}>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'security' && (
            <Card>
              <CardHeader>
                <CardTitle>Security</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Authentication</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                      <div>
                        <p className="font-medium text-slate-900">Two-Factor Authentication</p>
                        <p className="text-sm text-slate-500">Add an extra layer of security</p>
                      </div>
                      <Badge variant="info">Not Enabled</Badge>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                      <div>
                        <p className="font-medium text-slate-900">SSO / OIDC</p>
                        <p className="text-sm text-slate-500">Managed by Keycloak</p>
                      </div>
                      <Badge variant="success">Active</Badge>
                    </div>
                  </div>
                </div>
                <div className="pt-6 border-t border-slate-200">
                  <h3 className="text-lg font-medium text-slate-900 mb-4">API Keys</h3>
                  <p className="text-slate-500 mb-4">Manage API keys for programmatic access</p>
                  <div className="flex items-center gap-2">
                    <Button variant="outline">
                      <Key className="w-4 h-4 mr-2" />
                      Generate API Key
                    </Button>
                    <Button variant="ghost">Revoke All</Button>
                  </div>
                </div>
                <div className="pt-6 border-t border-slate-200">
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Active Sessions</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Server className="w-5 h-5 text-slate-400" />
                        <div>
                          <p className="font-medium text-slate-900">Current Session</p>
                          <p className="text-sm text-slate-500">Chrome on macOS · Active now</p>
                        </div>
                      </div>
                      <Badge variant="success">Current</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle>Notifications</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Email Notifications</h3>
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900">Enable email notifications</p>
                      <p className="text-sm text-slate-500">Receive alerts via email</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.emailNotifications}
                      onChange={(e) => setSettings({ ...settings, emailNotifications: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                    />
                  </label>
                </div>
                <div className="pt-4 border-t border-slate-200">
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Push Notifications</h3>
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900">Enable push notifications</p>
                      <p className="text-sm text-slate-500">Receive browser notifications</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.pushNotifications}
                      onChange={(e) => setSettings({ ...settings, pushNotifications: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                    />
                  </label>
                </div>
                <div className="pt-4 border-t border-slate-200">
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Alert Threshold</h3>
                  <select
                    value={settings.alertThreshold}
                    onChange={(e) => setSettings({ ...settings, alertThreshold: e.target.value })}
                    className="w-full max-w-md px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="info">All (Info + Warning + Critical)</option>
                    <option value="warning">Warning + Critical</option>
                    <option value="critical">Critical Only</option>
                  </select>
                </div>
                <div className="flex justify-end pt-4 border-t border-slate-200">
                  <Button onClick={handleSave}>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'appearance' && (
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Theme</h3>
                  <div className="grid gap-3 sm:grid-cols-3">
                    {(['light', 'dark', 'system'] as const).map((theme) => (
                      <button
                        key={theme}
                        onClick={() => setSettings({ ...settings, theme })}
                        className={cn(
                          'p-4 rounded-lg border-2 transition-colors text-left',
                          settings.theme === theme
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-slate-200 hover:border-slate-300'
                        )}
                      >
                        <div className="font-medium capitalize text-slate-900">{theme}</div>
                        <div className="text-sm text-slate-500 mt-1">
                          {theme === 'system' ? 'Matches OS setting' : `${theme} mode`}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="pt-4 border-t border-slate-200">
                  <h3 className="text-lg font-medium text-slate-900 mb-4">Display</h3>
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900">Compact mode</p>
                      <p className="text-sm text-slate-500">Reduce spacing for dense views</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.compactMode}
                      onChange={(e) => setSettings({ ...settings, compactMode: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                    />
                  </label>
                </div>
                <div className="flex justify-end pt-4 border-t border-slate-200">
                  <Button onClick={handleSave}>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

import { cn } from '../../lib/utils';