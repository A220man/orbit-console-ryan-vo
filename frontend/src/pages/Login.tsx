/** Login page */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Loader2, LogIn, Shield, Server, Activity } from 'lucide-react';
import { Button, Card, CardContent, Input } from '../ui';
import { useAuth } from '../../hooks';
import { cn } from '../../lib/utils';

export function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { checkAuth, isLoading: authLoading, isAuthenticated, login, oidcConfig } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for token in URL (from OIDC callback)
  useEffect(() => {
    const token = searchParams.get('token');
    const err = searchParams.get('error');
    const errDesc = searchParams.get('error_description');

    if (err) {
      setError(errDesc || err);
      return;
    }

    if (token) {
      // Token received from callback
      localStorage.setItem('access_token', token);
      checkAuth();
      navigate('/', { replace: true });
    }
  }, [searchParams, checkAuth, navigate]);

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [authLoading, isAuthenticated, navigate]);

  const handleLogin = () => {
    setIsLoading(true);
    setError(null);
    login();
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary-600" />
          <p className="text-slate-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-100 text-primary-600 mb-4">
              <Server className="w-8 h-8" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Orbit Console</h1>
            <p className="text-slate-500 mt-2">Agent Substrate Management</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
              {error}
            </div>
          )}

          <div className="space-y-4 mb-6">
            <div className="text-sm text-slate-500">
              Sign in with your organization account
            </div>
            <Button
              onClick={handleLogin}
              disabled={isLoading}
              className="w-full"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Redirecting...
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4 mr-2" />
                  Sign in with Keycloak
                </>
              )}
            </Button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-slate-500">Or continue with</span>
            </div>
          </div>

          <div className="mt-6 grid gap-3">
            <Button variant="outline" className="w-full" disabled>
              <Shield className="w-4 h-4 mr-2" />
              SSO (SAML/OIDC)
            </Button>
            <Button variant="outline" className="w-full" disabled>
              <Activity className="w-4 h-4 mr-2" />
              Local Development Mode
            </Button>
          </div>

          <div className="mt-8 text-center text-xs text-slate-400">
            <p>Orbit Console v1.0.0</p>
            <p>Ryan Vo <span>ryandtvo@gmail.com</span></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
