import { Chat } from '@/components/chat/Chat';
import { Loading } from '@/components/ui/loading';
import { ROUTE_PATHS } from '@/constants/path_routes';
import useAuth from '@/hooks/useAuth';
import { createFileRoute, Navigate } from '@tanstack/react-router';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading while checking authentication
  if (isLoading) {
    return <Loading message="Loading..." />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={ROUTE_PATHS.AUTH.LOGIN} />;
  }

  return <Chat />;
}
