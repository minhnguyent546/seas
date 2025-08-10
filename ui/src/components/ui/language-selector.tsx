import { Dropdown, DropdownItem } from '@/components/ui/dropdown';
import { useLanguage } from '@/hooks/useLanguage';
import { IconLanguage } from '@tabler/icons-react';

interface LanguageSelectorProps {
  variant?: 'default' | 'auth';
  className?: string;
}

export function LanguageSelector({
  variant = 'default',
  className = '',
}: LanguageSelectorProps) {
  const { currentLanguage, changeLanguage, availableLanguages, t } =
    useLanguage();

  const handleLanguageChange = async (languageCode: string) => {
    await changeLanguage(languageCode as 'en' | 'vi');
  };

  // Find the current language object to display its flag
  const currentLanguageObj = availableLanguages.find(
    (lang) => lang.code === currentLanguage,
  );

  const buttonBaseClasses =
    'h-8 w-8 rounded-full flex items-center justify-center transition-colors cursor-pointer';
  const buttonVariantClasses = {
    default: 'hover:bg-gray-200 dark:hover:bg-gray-700',
    auth: 'bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20',
  };

  return (
    <div className={className}>
      <Dropdown
        align="right"
        width="w-52"
        trigger={
          <button
            className={`${buttonBaseClasses} ${buttonVariantClasses[variant]}`}
          >
            {currentLanguageObj ? (
              <span className="text-lg">{currentLanguageObj.flag}</span>
            ) : (
              <IconLanguage
                size={16}
                className={
                  variant === 'auth'
                    ? 'text-white/80'
                    : 'text-gray-600 dark:text-gray-400'
                }
              />
            )}
          </button>
        }
      >
        <div className="px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-200 border-b border-gray-200 dark:border-gray-700">
          {t('nav.selectLanguage')}
        </div>
        {availableLanguages.map((language) => (
          <DropdownItem
            key={language.code}
            onClick={() => handleLanguageChange(language.code)}
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">{language.flag}</span>
              <span className="flex-1">{language.name}</span>
              {currentLanguage === language.code && (
                <div className="w-2 h-2 bg-primary rounded-full" />
              )}
            </div>
          </DropdownItem>
        ))}
      </Dropdown>
    </div>
  );
}
