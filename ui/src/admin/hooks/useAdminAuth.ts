import type { UserPublic } from '@/client';
import useAuth from '@/hooks/useAuth';
import { isAdminUser } from '@/lib/roles';

type useAdminAuthReturn = {
  user: UserPublic | null | undefined;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
};

export const useAdminAuth = (): useAdminAuthReturn => {
  const { user, isAuthenticated, isLoading } = useAuth();

  const isAdmin = isAuthenticated && isAdminUser(user);

  return {
    user,
    isAuthenticated,
    isLoading,
    isAdmin,
  };
};

export default useAdminAuth;
