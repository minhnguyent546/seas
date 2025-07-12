import type { ApiError } from '@/client';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines class names with Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Generates a unique ID
 */
export function generateId() {
  return Math.random().toString(36).substring(2, 9);
}

/**
 * Formats a date
 */
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
    hour12: true,
  }).format(date);
}

export const handleError = (error: ApiError) => {
  let errorMessage =
    error.body &&
    typeof error.body === 'object' &&
    'detail' in (error.body as Record<string, unknown>)
      ? (error.body as Record<string, unknown>).detail
      : 'Something went wrong';
  if (Array.isArray(errorMessage) && errorMessage.length > 0) {
    errorMessage = errorMessage[0];
  }
  // TODO: we might want to show toast message here

  console.debug(`API Error: ${error}`);
};
