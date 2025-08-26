import { AdminSessions } from '@/admin/components/sessions/AdminSessions';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/admin/sessions')({
  component: AdminSessions,
});
