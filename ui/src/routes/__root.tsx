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
    const isAuthRoute = location.pathname !== '/login';
    if (isAuthRoute && !isLoggedIn()) {
      throw redirect({
        to: '/login',
      });
    }

    // Redirect authenticated users to home if they try to access login
    if (location.pathname === '/login' && isLoggedIn()) {
      throw redirect({
        to: '/',
      });
    }
  },
  component: RootComponent,
});

function RootComponent() {
  const router = useRouter();

  // This ensures the router is aware of auth state changes
  useEffect(() => {
    const checkAuth = () => {
      // Force a reload of the current route when auth state changes
      router.invalidate();
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
