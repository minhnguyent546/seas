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
  beforeLoad: ({ location }) => {
    const isAuthPage =
      location.pathname === ROUTE_PATHS.AUTH.LOGIN ||
      location.pathname === ROUTE_PATHS.AUTH.SIGNUP;

    if (!isAuthPage && !isLoggedIn()) {
      throw redirect({
        to: ROUTE_PATHS.AUTH.LOGIN,
      });
    }

    if (isAuthPage && isLoggedIn()) {
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
        // Only trigger router invalidation if we're not already on the login/signup page
        // to avoid interfering with the login process
        if (
          window.location.pathname !== ROUTE_PATHS.AUTH.LOGIN &&
          window.location.pathname !== ROUTE_PATHS.AUTH.SIGNUP
        ) {
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
