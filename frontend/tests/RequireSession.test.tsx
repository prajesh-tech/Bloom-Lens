import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { RequireSession } from '../src/components/layout/RequireSession';
import { authApi } from '../src/services/authApi';

afterEach(() => { vi.restoreAllMocks(); });

it.each([true, false])('guards private content when authenticated=%s', async (authenticated) => {
  vi.spyOn(authApi, 'getSession').mockResolvedValue(authenticated ? { user_id: 'reviewer:1:alice', role: 'instructor' } : null);
  render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={['/private']}><Routes>
    <Route element={<RequireSession />}><Route path="/private" element={<p>Private content</p>} /></Route>
    <Route path="/login" element={<p>Login required</p>} />
  </Routes></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText(authenticated ? 'Private content' : 'Login required')).toBeInTheDocument();
  expect(screen.queryByText(authenticated ? 'Login required' : 'Private content')).not.toBeInTheDocument();
});
