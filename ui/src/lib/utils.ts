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

/**
 * Gets user-friendly error messages for different error types and HTTP status codes
 */
export async function getErrorMessage(
  error: unknown,
  response?: Response,
): Promise<string> {
  // Handle AbortError (when request is cancelled)
  if (error instanceof Error && error.name === 'AbortError') {
    return 'Request was cancelled';
  }

  // Handle network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return 'Unable to connect to the server. Please check your internet connection and try again.';
  }

  // Handle HTTP errors with response
  if (response && !response.ok) {
    try {
      // Try to parse error response body
      const errorData = await response.json();

      switch (response.status) {
        case 400:
          return (
            errorData.message ||
            'Invalid request. Please check your input and try again.'
          );
        case 401:
          return 'Authentication required. Please log in and try again.';
        case 403:
          return "Access denied. You don't have permission to perform this action.";
        case 404:
          return 'Service not found. Please contact support if this persists.';
        case 422:
          return (
            errorData.message ||
            'Invalid input provided. Please check your message and try again.'
          );
        case 429:
          return 'Too many requests. Please wait a moment and try again.';
        case 500:
          return 'Internal server error. Please try again later.';
        case 502:
          return 'Service temporarily unavailable. Please try again in a few moments.';
        case 503:
          return 'Service is currently under maintenance. Please try again later.';
        default:
          return (
            errorData.message ||
            `Server error (${response.status}). Please try again later.`
          );
      }
    } catch {
      // If we can't parse the response, fall back to status-based messages
      switch (response.status) {
        case 400:
          return 'Invalid request. Please check your input and try again.';
        case 401:
          return 'Authentication required. Please log in and try again.';
        case 403:
          return "Access denied. You don't have permission to perform this action.";
        case 404:
          return 'Service not found. Please contact support if this persists.';
        case 422:
          return 'Invalid input provided. Please check your message and try again.';
        case 429:
          return 'Too many requests. Please wait a moment and try again.';
        case 500:
          return 'Internal server error. Please try again later.';
        case 502:
          return 'Service temporarily unavailable. Please try again in a few moments.';
        case 503:
          return 'Service is currently under maintenance. Please try again later.';
        default:
          return `Server error (${response.status}). Please try again later.`;
      }
    }
  }

  // Handle other errors
  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
}
