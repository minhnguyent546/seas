import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

// Import translation files
import enTranslations from '@/locales/en/common.json';
import enPages from '@/locales/en/pages.json';
import viTranslations from '@/locales/vi/common.json';
import viPages from '@/locales/vi/pages.json';

// Define the resources
const resources = {
  en: {
    common: enTranslations,
    pages: enPages,
  },
  vi: {
    common: viTranslations,
    pages: viPages,
  },
} as const;

// Configure i18next
i18n
  .use(LanguageDetector) // Automatically detect user language
  .use(initReactI18next) // Initialize react-i18next
  .init({
    // Available languages
    supportedLngs: ['en', 'vi'],

    // Default language
    fallbackLng: 'en',

    // Language detection options
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },

    resources,

    // Default namespace
    defaultNS: 'common',

    // Interpolation options
    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // React specific options
    react: {
      useSuspense: false, // Disable suspense for easier setup
    },

    debug: import.meta.env.DEV,
  });

export default i18n;

export type SupportedLanguage = 'en' | 'vi';
export type TranslationKey = keyof typeof enTranslations;
