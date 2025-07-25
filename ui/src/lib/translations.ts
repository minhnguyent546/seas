import i18n from './i18n';

/**
 * Translation utility function that can be used outside of React components
 * @param key Translation key
 * @param options Translation options (interpolation, etc.)
 * @returns Translated string
 */
export function t(key: string, options?: any): string {
  return i18n.t(key, options) as string;
}

/**
 * Get the current language code
 * @returns Current language code
 */
export function getCurrentLanguage(): string {
  return i18n.language;
}

/**
 * Change the language programmatically
 * @param languageCode Language code to change to
 * @returns Promise that resolves when language change is complete
 */
export async function changeLanguage(languageCode: string): Promise<void> {
  await i18n.changeLanguage(languageCode);
}

/**
 * Check if a translation key exists
 * @param key Translation key to check
 * @returns True if key exists, false otherwise
 */
export function translationExists(key: string): boolean {
  return i18n.exists(key);
}

/**
 * Format a date according to the current locale
 * @param date Date to format
 * @param options Intl.DateTimeFormatOptions
 * @returns Formatted date string
 */
export function formatDate(
  date: Date | string | number,
  options?: Intl.DateTimeFormatOptions,
): string {
  const dateObj =
    typeof date === 'string' || typeof date === 'number'
      ? new Date(date)
      : date;
  const locale = getCurrentLanguage() === 'vi' ? 'vi-VN' : 'en-US';

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };

  return dateObj.toLocaleDateString(locale, { ...defaultOptions, ...options });
}

/**
 * Format a number according to the current locale
 * @param number Number to format
 * @param options Intl.NumberFormatOptions
 * @returns Formatted number string
 */
export function formatNumber(
  number: number,
  options?: Intl.NumberFormatOptions,
): string {
  const locale = getCurrentLanguage() === 'vi' ? 'vi-VN' : 'en-US';
  return number.toLocaleString(locale, options);
}

/**
 * Format currency according to the current locale
 * @param amount Amount to format
 * @param currency Currency code (default: USD)
 * @returns Formatted currency string
 */
export function formatCurrency(
  amount: number,
  currency: string = 'USD',
): string {
  const locale = getCurrentLanguage() === 'vi' ? 'vi-VN' : 'en-US';
  return amount.toLocaleString(locale, {
    style: 'currency',
    currency,
  });
}
