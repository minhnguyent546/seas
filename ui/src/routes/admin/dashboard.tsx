import { AdminDashboard } from '@/admin/components/dashboard/AdminDashboard';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/admin/dashboard')({
  component: AdminDashboard,
});
