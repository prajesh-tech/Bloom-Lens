import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { Login } from '../src/pages/Login';
import { authApi } from '../src/services/authApi';

afterEach(() => { vi.restoreAllMocks(); });
it('shows failed login then stores the successful session and opens the dashboard', async () => {
  const session = { user_id: 'reviewer:1:alice', role: 'instructor' };
  const login = vi.spyOn(authApi, 'login').mockRejectedValueOnce(new Error('Invalid credentials')).mockResolvedValue(session);
  const client = new QueryClient();
  const view = render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/login']}><Routes>
    <Route path="/login" element={<Login />} /><Route path="/" element={<h1>Dashboard</h1>} />
  </Routes></MemoryRouter></QueryClientProvider>);
  fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'a long password' } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials');
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByText('Dashboard')).toBeInTheDocument();
  expect(login).toHaveBeenCalledWith('alice', 'a long password');
  expect(client.getQueryData(['auth', 'session'])).toEqual(session);
  view.unmount(); client.clear();
});
