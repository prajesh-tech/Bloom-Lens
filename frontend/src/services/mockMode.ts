export const isMock = (): boolean => import.meta.env.VITE_USE_MOCK_API === 'true';
