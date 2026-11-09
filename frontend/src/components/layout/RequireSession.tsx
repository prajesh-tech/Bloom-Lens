import { useQuery } from '@tanstack/react-query';
import { Navigate, Outlet } from 'react-router-dom';
import { authApi } from '../../services/authApi';
import { Button } from '../common/Button';

export function RequireSession() {
  const session = useQuery({ queryKey: ['auth', 'session'], queryFn: authApi.getSession, retry: false });
  if (session.isPending) return <p role="status">Checking your session…</p>;
  if (session.isError) return <div role="alert">Unable to connect to BloomLens.
    <Button onClick={() => session.refetch()}>Retry</Button>
  </div>;
  if (!session.data) return <Navigate to="/login" replace />;
  return <Outlet />;
}
