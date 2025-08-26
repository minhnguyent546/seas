import App from '@/App';
import { ApiError, OpenAPI } from '@/client';
import { Loading } from '@/components/ui/loading';
import { ROUTE_PATHS } from '@/constants/routePaths';
import '@/lib/i18n'; // Initialize i18n
import { router } from '@/router';
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';
import { RouterProvider } from '@tanstack/react-router';

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';

const handleApiError = (error: Error) => {
  if (error instanceof ApiError && [401, 403].includes(error.status)) {
    // Only redirect if we're not already on auth pages
    const currentPath = window.location.pathname;
    const isOnAuthPage =
      currentPath === ROUTE_PATHS.AUTH.LOGIN ||
      currentPath === ROUTE_PATHS.AUTH.SIGNUP;

    if (!isOnAuthPage) {
      try {
        router.navigate({ to: ROUTE_PATHS.AUTH.LOGIN, replace: true });
      } catch {
        window.location.assign(ROUTE_PATHS.AUTH.LOGIN);
      }
    }
  }
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error) => {
        // Don't retry on auth errors
        if (error instanceof ApiError && [401, 403].includes(error.status)) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
});

// Configure OpenAPI client
const configureOpenAPI = () => {
  OpenAPI.BASE = import.meta.env.VITE_API_URL;
  if (!OpenAPI.BASE) {
    console.warn('VITE_API_URL is not set; API requests will fail.');
  }
  OpenAPI.CREDENTIALS = 'include';
  OpenAPI.WITH_CREDENTIALS = true;
};

// Register the router
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

// Wait for the router to be ready before rendering
async function prepareApp() {
  // Configure API client first
  configureOpenAPI();

  // Create the root element right away so we can show something immediately
  const rootElement = document.getElementById('root')!;
  const root = createRoot(rootElement);

  // Render a loading state first
  root.render(<Loading />);

  // Initialize the router in the background
  await router.load();

  // Render the full app once router is ready
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <App>
          <RouterProvider router={router} />
        </App>
      </QueryClientProvider>
    </StrictMode>,
  );
}

prepareApp();
