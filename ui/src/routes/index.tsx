import { Chat } from '@/components/chat/Chat';
import { Loading } from '@/components/ui/loading';
import { ROUTE_PATHS } from '@/constants/path_routes';
import useAuth from '@/hooks/useAuth';
import { usePageMeta } from '@/hooks/usePageTitle';
import { createFileRoute, Navigate } from '@tanstack/react-router';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  const { isAuthenticated, isLoading } = useAuth();

  // Set up page title and meta tags
  usePageMeta({
    titleKey: 'pages:titles.home',
    descriptionKey: 'pages:descriptions.home',
    fallbackTitle: 'Chat',
    fallbackDescription: 'CTU Enrollment Program',
  });

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
