import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/authApi';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const client = useQueryClient();
  const login = useMutation({
    mutationFn: () => authApi.login(username, password),
    onSuccess: (session) => { client.setQueryData(['auth', 'session'], session); setPassword(''); navigate('/', { replace: true }); },
  });
  return <main className="max-w-md mx-auto p-8">
    <Card><h1 className="text-2xl font-bold mb-4">Sign in to BloomLens</h1>
      <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); login.mutate(); }}>
        <label className="block">Username<input className="block border rounded p-2 w-full" autoComplete="username" required maxLength={100} value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <label className="block">Password<input className="block border rounded p-2 w-full" type="password" autoComplete="current-password" required maxLength={1024} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {login.error && <p role="alert">{login.error.message}</p>}
        <Button type="submit" isLoading={login.isPending}>Sign in</Button>
      </form>
    </Card>
  </main>;
}
