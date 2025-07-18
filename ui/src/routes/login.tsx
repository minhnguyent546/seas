import {
  OpenAPI,
  type Body_auth_login as BodyAuthLogin,
  type OAuthProvider,
} from '@/client';
import { GitHubIcon, GoogleIcon } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loading } from '@/components/ui/loading';
import { PasswordInput } from '@/components/ui/password-input';
import { ROUTE_PATHS } from '@/constants/path_routes';
import useAuth from '@/hooks/useAuth';
import { CircularProgress } from '@mui/material';
import { IconSparkles } from '@tabler/icons-react';
import { createFileRoute, Link, Navigate } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';

export const Route = createFileRoute('/login')({
  component: Login,
});

function Login() {
  const { loginMutation, error, resetError, isAuthenticated, isLoading } =
    useAuth();
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [googleError, setGoogleError] = useState<string | null>(null);
  const [isGitHubLoading, setIsGitHubLoading] = useState(false);
  const [gitHubError, setGitHubError] = useState<string | null>(null);
  const [oauthError, setOauthError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<BodyAuthLogin>({
    mode: 'onBlur',
    criteriaMode: 'all',
    defaultValues: {
      username: '',
      password: '',
    },
  });

  // Check for OAuth errors in URL parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const errorParam = urlParams.get('oauth2-error');
    const providerParam = urlParams.get('oauth2-provider') as OAuthProvider;
    const errorDescription = urlParams.get('error-description');

    if (errorParam) {
      const errorMessage = decodeURIComponent(errorDescription || errorParam);

      // Set provider-specific error based on the oauth2-provider parameter
      if (providerParam === 'GOOGLE') {
        setGoogleError(errorMessage);
      } else if (providerParam === 'GITHUB') {
        setGitHubError(errorMessage);
      } else {
        setOauthError(errorMessage);
      }

      // Clean up URL parameters
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, []);

  // Show loading while checking authentication
  if (isLoading) {
    return <Loading message="Checking authentication..." />;
  }

  // Redirect to home if already authenticated
  if (isAuthenticated) {
    return <Navigate to={ROUTE_PATHS.HOME} />;
  }

  const onSubmit: SubmitHandler<BodyAuthLogin> = async (
    data: BodyAuthLogin,
  ) => {
    if (isSubmitting || loginMutation.isPending) return;

    resetError();
    setGoogleError(null); // Clear Google error when attempting regular login
    setGitHubError(null); // Clear GitHub error when attempting regular login
    setOauthError(null); // Clear OAuth error when attempting regular login
    try {
      await loginMutation.mutateAsync(data);
    } catch {
      // Error handling is done in the mutation's onError callback
    }
  };

  const handleGoogleLogin = async () => {
    if (isGoogleLoading) return;

    setIsGoogleLoading(true);
    setGoogleError(null); // Clear previous Google errors
    setGitHubError(null); // Clear GitHub errors
    setOauthError(null); // Clear OAuth errors
    resetError(); // Clear regular login errors

    try {
      // await AuthService.loginViaGoogleOauth2();

      // TODO: currently hardcoded as redirect response probably not working with http
      const baseUrl = OpenAPI.BASE;
      const googleOAuthUrl = `${baseUrl}/api/v1/auth/login/google-oauth2`;
      window.location.href = googleOAuthUrl;
    } catch (error) {
      console.error('Google OAuth login failed:', error);

      // Extract error message
      let errorMessage = 'Google login failed. Please try again.';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error && typeof error === 'object' && 'message' in error) {
        errorMessage = String(error.message);
      }

      setGoogleError(errorMessage);
      setIsGoogleLoading(false);
    }
  };

  const handleGitHubLogin = async () => {
    if (isGitHubLoading) return;

    setIsGitHubLoading(true);
    setGitHubError(null); // Clear previous GitHub errors
    setGoogleError(null); // Clear Google errors
    setOauthError(null); // Clear OAuth errors
    resetError(); // Clear regular login errors

    try {
      // TODO: currently hardcoded as redirect response probably not working with http
      const baseUrl = OpenAPI.BASE;
      const gitHubOAuthUrl = `${baseUrl}/api/v1/auth/login/github-oauth2`;
      window.location.href = gitHubOAuthUrl;
    } catch (error) {
      console.error('GitHub OAuth login failed:', error);

      // Extract error message
      let errorMessage = 'GitHub login failed. Please try again.';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error && typeof error === 'object' && 'message' in error) {
        errorMessage = String(error.message);
      }

      setGitHubError(errorMessage);
      setIsGitHubLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-cover bg-center"
      style={{
        backgroundImage: 'url("/images/ctu-background.jpg")',
        backgroundColor: 'rgba(0,0,0,0.5)',
        backgroundBlendMode: 'overlay',
      }}
    >
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-xl">
        <div className="text-center">
          <h1 className="mb-5 flex items-center justify-center gap-2 text-4xl font-bold text-blue-600">
            <IconSparkles className="h-12 w-12" />
            <span>CTU SEAS</span>
          </h1>
          <h2 className="text-3xl font-bold text-gray-900">Sign in</h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to your account to continue
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-700"
              >
                Username
              </label>
              <Input
                id="username"
                type="text"
                autoComplete="username"
                required
                placeholder="Enter your username"
                error={errors.username?.message}
                {...register('username', {
                  required: 'Username is required',
                  minLength: {
                    value: 3,
                    message: 'Username must be at least 3 characters',
                  },
                })}
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <PasswordInput
                id="password"
                autoComplete="current-password"
                required
                placeholder="Enter your password"
                error={errors.password?.message}
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 6,
                    message: 'Password must be at least 6 characters',
                  },
                })}
              />
            </div>
          </div>
          {(error || googleError || gitHubError || oauthError) && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error || googleError || gitHubError || oauthError}
            </div>
          )}
          <Button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 cursor-pointer disabled:cursor-not-allowed"
            isLoading={isSubmitting || loginMutation.isPending}
            disabled={isSubmitting || loginMutation.isPending}
          >
            {isSubmitting || loginMutation.isPending
              ? 'Signing in...'
              : 'Sign in'}
          </Button>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-gray-500">Or</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full border-gray-300 bg-white text-gray-700 hover:bg-gray-50 cursor-pointer disabled:cursor-not-allowed"
            onClick={handleGoogleLogin}
            disabled={isGoogleLoading}
          >
            <GoogleIcon className="mr-2" size={20} />
            {isGoogleLoading ? (
              <>
                Signing in with Google
                <CircularProgress size={16} className="ml-2" />
              </>
            ) : (
              'Continue with Google'
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            className="w-full border-gray-300 bg-white text-gray-700 hover:bg-gray-50 cursor-pointer disabled:cursor-not-allowed"
            onClick={handleGitHubLogin}
            disabled={isGitHubLoading}
          >
            <GitHubIcon className="mr-2" size={20} />
            {isGitHubLoading ? (
              <>
                Signing in with GitHub
                <CircularProgress size={16} className="ml-2" />
              </>
            ) : (
              'Continue with GitHub'
            )}
          </Button>
        </form>
        <div className="text-center text-sm mt-4">
          Don't have an account?{' '}
          <Link to="/signup" className="text-primary hover:underline">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
