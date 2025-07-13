import { ROUTE_PATHS } from '@/constants/path_routes';
import { isLoggedIn } from '@/hooks/useAuth';
import {
  Outlet,
  createRootRoute,
  redirect,
  useRouter,
} from '@tanstack/react-router';
import { useEffect } from 'react';

export const Route = createRootRoute({
  // This is executed before the route is even loaded
  beforeLoad: ({ location }) => {
    // Redirect unauthenticated users to login page if they're trying to access protected routes
    const isAuthRoute = location.pathname !== ROUTE_PATHS.AUTH.LOGIN;
    if (isAuthRoute && !isLoggedIn()) {
      throw redirect({
        to: ROUTE_PATHS.AUTH.LOGIN,
      });
    }

    // Redirect authenticated users to home if they try to access login
    if (location.pathname === ROUTE_PATHS.AUTH.LOGIN && isLoggedIn()) {
      throw redirect({
        to: ROUTE_PATHS.HOME,
      });
    }
  },
  component: RootComponent,
});

function RootComponent() {
  const router = useRouter();

  // This ensures the router is aware of auth state changes from other tabs
  useEffect(() => {
    const checkAuth = (event: StorageEvent) => {
      // Only invalidate router if the access_token was removed/added
      if (event.key === 'access_token') {
        // Only trigger router invalidation if we're not already on the login page
        // to avoid interfering with the login process
        if (window.location.pathname !== ROUTE_PATHS.AUTH.LOGIN) {
          router.invalidate();
        }
      }
    };

    // Listen for storage events (logout/login in other tabs)
    window.addEventListener('storage', checkAuth);

    return () => {
      window.removeEventListener('storage', checkAuth);
    };
  }, [router]);

  return (
    <>
      <Outlet />
    </>
  );
}
