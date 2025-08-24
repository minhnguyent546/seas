import { AdminUsers } from '@/admin/components/users/AdminUsers';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/admin/users')({
  component: AdminUsersPage,
});

function AdminUsersPage() {
  return <AdminUsers />;
}
