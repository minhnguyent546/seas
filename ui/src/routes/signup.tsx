import { type UserRegister } from '@/client';
import { SeasLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LanguageSelector } from '@/components/ui/language-selector';
import { PasswordInput } from '@/components/ui/password-input';
import { ROUTE_PATHS } from '@/constants/routePaths';
import useAuth from '@/hooks/useAuth';
import { useLanguage } from '@/hooks/useLanguage';
import { usePageMeta } from '@/hooks/usePageTitle';
import {
  Link,
  Navigate,
  createFileRoute,
  useNavigate,
} from '@tanstack/react-router';
import { useForm, type SubmitHandler } from 'react-hook-form';

export const Route = createFileRoute('/signup')({
  component: SignupComponent,
});

function SignupComponent() {
  const { signupMutation, error, resetError, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { t } = useLanguage();

  // Set up page title and meta tags
  usePageMeta({
    titleKey: 'pages:titles.signup',
    descriptionKey: 'pages:descriptions.signup',
    fallbackTitle: 'Sign Up',
    fallbackDescription: 'Sign up to ask about the CTU Enrollment Program',
  });

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

  // Redirect to home if already authenticated
  if (isAuthenticated) {
    return <Navigate to={ROUTE_PATHS.HOME} replace={true} />;
  }

  const onSubmit: SubmitHandler<UserRegister> = async (data: UserRegister) => {
    if (isSubmitting || signupMutation.isPending) return;

    resetError();
    try {
      await signupMutation.mutateAsync(data);
      navigate({ to: ROUTE_PATHS.AUTH.LOGIN });
    } catch {
      // Error handling is done in the mutation's onError callback
    }
  };

  return (
    <div
      className="w-full flex items-center justify-center bg-cover bg-center relative h-fluid md:min-h-screen"
      style={{
        backgroundImage: 'url("/images/ctu-background.jpg")',
        backgroundColor: 'rgba(0,0,0,0.5)',
        backgroundBlendMode: 'overlay',
      }}
    >
      {/* Language Selector */}
      <LanguageSelector
        variant="auth"
        className="absolute top-4 right-4 z-10"
      />

      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-none md:rounded-lg shadow-xl h-full max-h-fluid overflow-auto md:h-auto md:max-h-none md:overflow-visible">
        <div className="text-center">
          <h1 className="mb-5 flex items-center justify-center gap-2 text-4xl font-bold text-blue-600">
            <SeasLogo size={48} className="text-primary" />
            <span>CTU SEAS</span>
          </h1>
          <h2 className="text-3xl font-bold text-gray-900">
            {t('auth.createAccount')}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {t('auth.createAccountSubtext')}
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="fullName"
                className="block text-sm font-medium text-gray-700 dark:text-gray-100"
              >
                {t('auth.fullName')}
              </label>
              <Input
                id="fullName"
                type="text"
                autoComplete="name"
                required
                placeholder={t('auth.placeholders.enterFullName')}
                error={errors.full_name?.message}
                {...register('full_name', {
                  required: t('auth.validation.fullNameRequired'),
                  minLength: {
                    value: 3,
                    message: t('auth.validation.fullNameMinLength'),
                  },
                })}
              />
            </div>
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-700 dark:text-gray-100"
              >
                {t('auth.username')}
              </label>
              <Input
                id="username"
                type="text"
                autoComplete="username"
                required
                placeholder={t('auth.placeholders.enterUsername')}
                error={errors.username?.message}
                {...register('username', {
                  required: t('auth.validation.usernameRequired'),
                  minLength: {
                    value: 3,
                    message: t('auth.validation.usernameMinLength'),
                  },
                })}
              />
            </div>
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 dark:text-gray-100"
              >
                {t('auth.emailAddress')}
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                placeholder={t('auth.placeholders.enterEmail')}
                error={errors.email?.message}
                {...register('email', {
                  required: t('auth.validation.emailRequired'),
                  pattern: {
                    value:
                      /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i,
                    message: t('auth.validation.emailInvalid'),
                  },
                })}
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 dark:text-gray-100"
              >
                {t('auth.password')}
              </label>
              <PasswordInput
                id="password"
                autoComplete="new-password"
                required
                placeholder={t('auth.placeholders.enterPassword')}
                error={errors.password?.message}
                {...register('password', {
                  required: t('auth.validation.passwordRequired'),
                  minLength: {
                    value: 6,
                    message: t('auth.validation.passwordMinLength'),
                  },
                })}
              />
            </div>
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700 dark:text-gray-100"
              >
                {t('auth.confirmPassword')}
              </label>
              <PasswordInput
                id="confirmPassword"
                autoComplete="new-password"
                required
                placeholder={t('auth.placeholders.confirmPassword')}
                error={errors.confirmPassword?.message}
                {...register('confirmPassword', {
                  required: t('auth.validation.confirmPasswordRequired'),
                  validate: (value) =>
                    value === password || t('auth.validation.passwordsNoMatch'),
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
            className="w-full bg-blue-600 hover:bg-blue-700 cursor-pointer disabled:cursor-not-allowed"
            isLoading={isSubmitting || signupMutation.isPending}
            disabled={isSubmitting || signupMutation.isPending}
          >
            {isSubmitting || signupMutation.isPending
              ? t('auth.creatingAccount')
              : t('auth.createAccountButton')}
          </Button>
        </form>
        <div className="text-center text-sm mt-4 text-gray-700 dark:text-gray-100">
          {t('auth.alreadyHaveAccount')}{' '}
          <Link
            to={ROUTE_PATHS.AUTH.LOGIN}
            className="text-primary hover:underline"
          >
            {t('auth.signIn')}
          </Link>
        </div>
      </div>
    </div>
  );
}
