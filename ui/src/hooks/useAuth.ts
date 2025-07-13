import {
  type Body_auth_login_for_access_token as AccessToken,
  type ApiError,
  AuthService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from '@/client';
import { ROUTE_PATHS } from '@/constants/path_routes';
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
      navigate({ to: ROUTE_PATHS.AUTH.LOGIN });
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
  };

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      setError(null);
      navigate({ to: ROUTE_PATHS.HOME });
      // Force a re-render by invalidating the current user query
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
    onError: (error: ApiError) => {
      const errorMessage =
        error.body &&
        typeof error.body === 'object' &&
        'detail' in (error.body as Record<string, unknown>)
          ? (error.body as Record<string, unknown>).detail
          : 'Incorrect username or password';

      let message =
        typeof errorMessage === 'string'
          ? errorMessage
          : 'Incorrect username or password';
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

    // Navigate to login page
    navigate({ to: ROUTE_PATHS.AUTH.LOGIN });

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
