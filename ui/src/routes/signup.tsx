import { type UserRegister } from '@/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PasswordInput } from '@/components/ui/password-input';
import useAuth from '@/hooks/useAuth';
import { IconSparkles } from '@tabler/icons-react';
import { Link, createFileRoute, useNavigate } from '@tanstack/react-router';
import { useForm, type SubmitHandler } from 'react-hook-form';

export const Route = createFileRoute('/signup')({
  component: SignupComponent,
});

function SignupComponent() {
  const { signupMutation, error, resetError } = useAuth();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<UserRegister & { confirmPassword?: string }>({
    mode: 'onBlur',
    criteriaMode: 'all',
    defaultValues: {
      username: '',
      email: '',
      full_name: '',
      password: '',
      confirmPassword: '',
    },
  });

  const password = watch('password');

  const onSubmit: SubmitHandler<UserRegister> = async (data: UserRegister) => {
    if (isSubmitting || signupMutation.isPending) return;

    resetError();
    try {
      await signupMutation.mutateAsync(data);
      navigate({ to: '/login' });
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
          <h1 className="mb-5 flex items-center justify-center gap-2 text-4xl font-bold text-blue-600">
            <IconSparkles className="h-12 w-12" />
            <span>CTU SEAS</span>
          </h1>
          <h2 className="text-3xl font-bold text-gray-900">
            Create an account
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Join us to explore the CTU Enrollment Program
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="fullName"
                className="block text-sm font-medium text-gray-700"
              >
                Full Name
              </label>
              <Input
                id="fullName"
                type="text"
                autoComplete="name"
                required
                placeholder="Enter your full name"
                error={errors.full_name?.message}
                {...register('full_name', {
                  required: 'Full name is required',
                  minLength: {
                    value: 3,
                    message: 'Full name must be at least 3 characters',
                  },
                })}
              />
            </div>
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
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email address
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                placeholder="Enter your email"
                error={errors.email?.message}
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value:
                      /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i,
                    message: 'Invalid email address',
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
                autoComplete="new-password"
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
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700"
              >
                Confirm Password
              </label>
              <PasswordInput
                id="confirmPassword"
                autoComplete="new-password"
                required
                placeholder="Confirm your password"
                error={errors.confirmPassword?.message}
                {...register('confirmPassword', {
                  required: 'Please confirm your password',
                  validate: (value) =>
                    value === password || 'Passwords do not match',
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
            isLoading={isSubmitting || signupMutation.isPending}
            disabled={isSubmitting || signupMutation.isPending}
          >
            {isSubmitting || signupMutation.isPending
              ? 'Creating account...'
              : 'Create account'}
          </Button>
        </form>
        <div className="text-center text-sm mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
