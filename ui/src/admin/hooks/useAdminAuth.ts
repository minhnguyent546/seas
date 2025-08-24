import type { UserPublic } from '@/client';
import useAuth from '@/hooks/useAuth';

type useAdminAuthReturn = {
  user: UserPublic | null | undefined;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
};

export const useAdminAuth = (): useAdminAuthReturn => {
  const { user, isAuthenticated, isLoading } = useAuth();

  const isAdmin = isAuthenticated && user?.role === 'ADMIN';

  return {
    user,
    isAuthenticated,
    isLoading,
    isAdmin,
  };
};

export default useAdminAuth;
