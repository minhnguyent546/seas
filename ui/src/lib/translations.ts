import i18n from '@/lib/i18n';

/**
 * Get current language code
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
 * Check if a translation exists for the given key
 * @param key Translation key to check
 * @returns True if translation exists
 */
export function translationExists(key: string): boolean {
  return i18n.exists(key);
}

/**
 * Format a date according to en-US locale
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

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };

  return dateObj.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

/**
 * Format a number according to en-US locale
 * @param number Number to format
 * @param options Intl.NumberFormatOptions
 * @returns Formatted number string
 */
export function formatNumber(
  number: number,
  options?: Intl.NumberFormatOptions,
): string {
  return number.toLocaleString('en-US', options);
}

/**
 * Format currency according to en-US locale
 * @param amount Amount to format
 * @param currency Currency code (default: USD)
 * @returns Formatted currency string
 */
export function formatCurrency(
  amount: number,
  currency: string = 'USD',
): string {
  return amount.toLocaleString('en-US', {
    style: 'currency',
    currency,
  });
}
