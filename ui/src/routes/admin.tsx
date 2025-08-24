import { AdminLayout } from '@/admin/components/layout/AdminLayout';
import useAdminAuth from '@/admin/hooks/useAdminAuth';
import { Loading } from '@/components/ui/loading';
import { ROUTE_PATHS } from '@/constants/routePaths';
import { createFileRoute, Navigate, Outlet } from '@tanstack/react-router';

export const Route = createFileRoute('/admin')({
  component: AdminRouteComponent,
});

function AdminRouteComponent() {
  const { isAuthenticated, isLoading, isAdmin } = useAdminAuth();

  if (isLoading) {
    return <Loading message="Loading Admin Panel..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTE_PATHS.AUTH.LOGIN} />;
  }

  if (!isAdmin) {
    return <Navigate to={ROUTE_PATHS.HOME} />;
  }

  return (
    <AdminLayout>
      <Outlet />
    </AdminLayout>
  );
}
