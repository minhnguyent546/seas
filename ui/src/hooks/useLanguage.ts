import type { SupportedLanguage } from '@/lib/i18n';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

export interface Language {
  code: SupportedLanguage;
  name: string;
  flag: string;
}

export const LANGUAGES: Language[] = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
] as const;

export function useLanguage() {
  const { i18n, t } = useTranslation();

  const currentLanguage = i18n.language as SupportedLanguage;

  const changeLanguage = useCallback(
    async (languageCode: SupportedLanguage) => {
      try {
        await i18n.changeLanguage(languageCode);
      } catch (error) {
        console.error('Failed to change language:', error);
      }
    },
    [i18n],
  );

  const getCurrentLanguage = useCallback((): Language => {
    return (
      LANGUAGES.find((lang) => lang.code === currentLanguage) || LANGUAGES[0]
    );
  }, [currentLanguage]);

  const getLanguageName = useCallback(
    (code: SupportedLanguage): string => {
      return t(`languages.${code}`);
    },
    [t],
  );

  return {
    currentLanguage,
    changeLanguage,
    getCurrentLanguage,
    getLanguageName,
    availableLanguages: LANGUAGES,
    t,
  };
}
