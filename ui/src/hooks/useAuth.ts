import {
  type Body_auth_login_for_access_token as AccessToken,
  type ApiError,
  AuthService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from '@/client';
import { handleError } from '@/lib/utils';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { useState } from 'react';

const isLoggedIn = () => {
  return localStorage.getItem('access_token') !== null;
};

const useAuth = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ['currentUser'],
    queryFn: UsersService.getUserMe,
    enabled: isLoggedIn(),
  });

  const signupMutation = useMutation({
    mutationFn: async (data: UserRegister) => {
      await AuthService.signup({ requestBody: data });
    },
    onSuccess: () => {
      navigate({ to: '/login' });
    },
    onError: (err: ApiError) => {
      handleError(err);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const login = async (data: AccessToken) => {
    const response = await AuthService.loginForAccessToken({ formData: data });
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('token_type', response.token_type || 'Bearer');

    // No need to update OpenAPI.TOKEN here as it's configured in main.tsx to read from localStorage
  };

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      setError(null);
      navigate({ to: '/' });
      // Force a re-render by invalidating the current user query
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
    onError: (error: ApiError) => {
      const errorMessage =
        error.body &&
        typeof error.body === 'object' &&
        'detail' in (error.body as Record<string, unknown>)
          ? (error.body as Record<string, unknown>).detail
          : 'Login failed. Please check your credentials.';

      let message =
        typeof errorMessage === 'string'
          ? errorMessage
          : 'Login failed. Please check your credentials.';
      if (Array.isArray(errorMessage) && errorMessage.length > 0) {
        message = String(errorMessage[0]);
      }

      setError(message);
      handleError(error);
    },
  });

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');

    // No need to set OpenAPI.TOKEN to undefined as it's configured in main.tsx to read from localStorage
    // which will now return an empty string

    // Navigate to login page
    navigate({ to: '/login' });

    // Clear user data and force re-render
    queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    queryClient.clear(); // Clear all cached data
  };

  return {
    signupMutation,
    loginMutation,
    logout,
    user,
    error,
    resetError: () => setError(null),
  };
};

export { isLoggedIn };
export default useAuth;
