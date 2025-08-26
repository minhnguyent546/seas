import {
  ApiError,
  AuthService,
  UsersService,
  type Body_auth_login as BodyAuthLogin,
  type UserPublic,
  type UserRegister,
} from '@/client';
import { ROUTE_PATHS } from '@/constants/routePaths';
import { router } from '@/router';
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
} from '@tanstack/react-query';
import { useState } from 'react';

// Authentication query keys
export const AUTH_QUERY_KEYS = {
  currentUser: ['currentUser'] as const,
  users: ['users'] as const,
} as const;

export type AuthState = {
  user: UserPublic | null | undefined;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
};

export type AuthActions = {
  signupMutation: UseMutationResult<void, Error, UserRegister>;
  loginMutation: UseMutationResult<void, Error, BodyAuthLogin>;
  logout: () => Promise<void>;
  resetError: () => void;
};

// Helper function to extract error message from API error
const extractErrorMessage = (
  error: ApiError,
  fallback = 'Something went wrong',
): string => {
  if (!error.body || typeof error.body !== 'object') {
    return fallback;
  }

  const body = error.body as Record<string, unknown>;
  const detail = body.detail;

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return String(detail[0]);
  }

  return fallback;
};

// Check if user is authenticated based on current user query
export const useAuthStatus = () => {
  const userQuery = useQuery<UserPublic | null, Error>({
    queryKey: AUTH_QUERY_KEYS.currentUser,
    queryFn: UsersService.getUserMe,
    retry: (failureCount, error) => {
      // Don't retry on auth errors
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        return false;
      }
      return failureCount < 2;
    },
    refetchOnWindowFocus: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  return {
    user: userQuery.data,
    isAuthenticated: !!userQuery.data,
    isLoading: userQuery.isLoading,
    isError: userQuery.isError,
    error: userQuery.error,
  };
};

const useAuth = (): AuthState & AuthActions => {
  const [authError, setAuthError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading } = useAuthStatus();

  // Signup mutation
  const signupMutation = useMutation({
    mutationFn: async (data: UserRegister) => {
      await AuthService.signup({ requestBody: data });
    },
    onSuccess: () => {
      setAuthError(null);
      router.navigate({ to: ROUTE_PATHS.AUTH.LOGIN });
    },
    onError: (error: ApiError) => {
      const message = extractErrorMessage(error, 'Failed to create account');
      setAuthError(message);
      console.error('Signup error:', error);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: AUTH_QUERY_KEYS.users });
    },
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (data: BodyAuthLogin) => {
      await AuthService.login({ formData: data });
    },
    onSuccess: async () => {
      setAuthError(null);
      // Invalidate and refetch current user to update auth state
      await queryClient.invalidateQueries({
        queryKey: AUTH_QUERY_KEYS.currentUser,
        refetchType: 'active',
      });
      await queryClient.refetchQueries({
        queryKey: AUTH_QUERY_KEYS.currentUser,
      });
      router.navigate({ to: ROUTE_PATHS.HOME });
    },
    onError: (error: ApiError) => {
      const message = extractErrorMessage(
        error,
        'Incorrect username or password',
      );
      setAuthError(message);
      console.error('Login error:', error);
    },
  });

  // Logout function
  const logout = async () => {
    try {
      await AuthService.signout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear all cached data and navigate to login
      queryClient.clear();
      router.navigate({ to: ROUTE_PATHS.AUTH.LOGIN });
    }
  };

  return {
    // Auth state
    user,
    isAuthenticated,
    isLoading,
    error: authError,

    // Mutations
    signupMutation,
    loginMutation,

    // Actions
    logout,
    resetError: () => setAuthError(null),
  };
};

export default useAuth;
