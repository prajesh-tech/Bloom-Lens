import { Toaster as SonnerToaster, toast as sonnerToast } from 'sonner';
import { useTheme } from '../../context/ThemeContext';

export const Toaster = () => {
  const { theme } = useTheme();

  return (
    <SonnerToaster
      position="bottom-right"
      theme={theme}
      toastOptions={{
        className: 'font-sans text-sm border border-slate-200 dark:border-slate-800 shadow-lg rounded-xl dark:bg-slate-900 dark:text-slate-100',
      }}
    />
  );
};

export const toast = {
  success: (message: string) => sonnerToast.success(message),
  error: (message: string) => sonnerToast.error(message),
  info: (message: string) => sonnerToast.info(message),
  warning: (message: string) => sonnerToast.warning(message),
};
