import { ROUTE_PATHS } from '@/constants/routePaths';
import { createFileRoute, Navigate } from '@tanstack/react-router';

export const Route = createFileRoute('/admin/')({
  component: AdminIndexPage,
});

function AdminIndexPage() {
  return <Navigate to={ROUTE_PATHS.ADMIN.DASHBOARD} replace />;
}
