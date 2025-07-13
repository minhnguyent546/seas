import { type Body_auth_login_for_access_token as AccessToken } from '@/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import useAuth from '@/hooks/useAuth';
import { createFileRoute } from '@tanstack/react-router';
import { useForm, type SubmitHandler } from 'react-hook-form';

export const Route = createFileRoute('/login')({
  component: Login,
});

function Login() {
  const { loginMutation, error, resetError } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AccessToken>({
    mode: 'onBlur',
    criteriaMode: 'all',
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const onSubmit: SubmitHandler<AccessToken> = async (data: AccessToken) => {
    if (isSubmitting) return;

    resetError();
    try {
      await loginMutation.mutateAsync(data);
    } catch {
      // Error handling is done in the mutation's onError callback
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
          <h1 className="text-4xl font-bold text-blue-600 mb-2">CTU SEAS</h1>
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
              <Input
                id="password"
                type="password"
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
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          <Button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700"
            isLoading={isSubmitting || loginMutation.isPending}
            disabled={isSubmitting || loginMutation.isPending}
          >
            {isSubmitting || loginMutation.isPending
              ? 'Signing in...'
              : 'Sign in'}
          </Button>
        </form>
        {/* Example: Add a signup link if needed */}
        {/* <div className="text-center text-sm mt-4">
          Don't have an account?{' '}
          <Link to="/signup" className="text-primary hover:underline">Sign up</Link>
        </div> */}
      </div>
    </div>
  );
}
