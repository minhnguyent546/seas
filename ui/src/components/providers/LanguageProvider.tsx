import { useLanguage } from '@/hooks/useLanguage';
import { useEffect, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface LanguageProviderProps {
  children: ReactNode;
}

export function LanguageProvider({ children }: LanguageProviderProps) {
  const { currentLanguage } = useLanguage();
  const { i18n } = useTranslation();

  // Update HTML lang attribute when language changes
  useEffect(() => {
    document.documentElement.lang = currentLanguage;
  }, [currentLanguage]);

  // Update text direction for RTL languages (future-proofing)
  useEffect(() => {
    const isRTL = ['ar', 'he', 'fa'].includes(currentLanguage);
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
  }, [currentLanguage]);

  // Set up language change event listeners
  useEffect(() => {
    const handleLanguageChange = (lng: string) => {
      document.documentElement.lang = lng;
    };

    i18n.on('languageChanged', handleLanguageChange);

    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);

  return <>{children}</>;
}
