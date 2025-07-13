import { cn } from '@/lib/utils';
import { CircularProgress } from '@mui/material';
import * as React from 'react';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'tertiary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      children,
      ...props
    },
    ref,
  ) => {
    const baseStyles =
      'seas-btn inline-flex items-center justify-center rounded-xl font-medium transition focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50';

    const variants = {
      primary:
        'bg-primary text-white hover:bg-primary-700 focus:ring-primary-500',
      secondary:
        'bg-secondary text-white hover:bg-secondary hover:brightness-95 focus:ring-secondary',
      tertiary:
        'bg-tertiary text-white hover:bg-tertiary hover:brightness-95 focus:ring-tertiary',
      outline:
        'border border-gray-300 bg-transparent hover:bg-gray-100 focus:ring-gray-500',
      ghost: 'bg-transparent hover:bg-gray-100 focus:ring-gray-500',
    };

    const sizes = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-4 text-sm',
      lg: 'h-12 px-6 text-base',
      icon: 'h-10 w-10',
    };

    return (
      <button
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          isLoading && 'cursor-not-allowed opacity-70',
          className,
        )}
        ref={ref}
        disabled={isLoading || props.disabled}
        {...props}
      >
        {isLoading ? (
          <CircularProgress
            size={size === 'sm' ? 16 : size === 'lg' ? 20 : 18}
            sx={{ mr: 1, color: 'inherit' }}
          />
        ) : null}
        {children}
      </button>
    );
  },
);
Button.displayName = 'Button';

export { Button };
