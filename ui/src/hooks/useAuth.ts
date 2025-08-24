import {
  ApiError,
  AuthService,
  type Body_auth_login as BodyAuthLogin,
  type UserPublic,
  type UserRegister,
  UsersService,
} from '@/client';
import { ROUTE_PATHS } from '@/constants/routePaths';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { useState } from 'react';

// Authentication query keys
export const AUTH_QUERY_KEYS = {
  currentUser: ['currentUser'] as const,
  users: ['users'] as const,
} as const;

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

const useAuth = () => {
  const [authError, setAuthError] = useState<string | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading } = useAuthStatus();

  // Signup mutation
  const signupMutation = useMutation({
    mutationFn: async (data: UserRegister) => {
      await AuthService.signup({ requestBody: data });
    },
    onSuccess: () => {
      setAuthError(null);
      navigate({ to: ROUTE_PATHS.AUTH.LOGIN });
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
    onSuccess: () => {
      setAuthError(null);
      // Invalidate and refetch current user to update auth state
      queryClient.invalidateQueries({ queryKey: AUTH_QUERY_KEYS.currentUser });
      navigate({ to: ROUTE_PATHS.HOME });
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
      navigate({ to: ROUTE_PATHS.AUTH.LOGIN });
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
