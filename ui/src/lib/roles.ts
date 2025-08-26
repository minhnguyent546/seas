import type { UserPublic } from '@/client';

export const isAdminUser = (user: UserPublic | null | undefined): boolean => {
  if (!user || !user.role) return false;
  return user.role === 'ADMIN';
};
