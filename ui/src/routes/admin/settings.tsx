import { AdminSettings } from '@/admin/components/settings/AdminSettings';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/admin/settings')({
  component: AdminSettings,
});
