import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Dropdown,
  DropdownItem,
  DropdownSeparator,
} from '@/components/ui/dropdown';
import useAuth from '@/hooks/useAuth';
import { useLanguage } from '@/hooks/useLanguage';
import { IconLanguage, IconLogout, IconSettings } from '@tabler/icons-react';
import { useState } from 'react';

export function UserControls() {
  const { user, logout } = useAuth();
  const { currentLanguage, changeLanguage, availableLanguages, t } =
    useLanguage();
  const [testUser] = useState({
    id: '1',
    name: 'Test user',
    image: undefined,
  });

  const handleSettings = () => {
    console.log('Settings clicked');
    // Implementation would open settings panel
  };

  const handleLanguageChange = async (languageCode: string) => {
    await changeLanguage(languageCode as 'en' | 'vi');
  };

  if (!user) {
    return null;
  }

  const userName = user.full_name || user.email || 'User';
  const userInitials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  return (
    <div className="absolute top-4 right-4 z-10 flex items-center gap-3">
      {/* Language Toggle Button */}
      <Dropdown
        align="right"
        width="w-52"
        trigger={
          <button className="h-8 w-8 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 flex items-center justify-center transition-colors cursor-pointer">
            <IconLanguage
              size={16}
              className="text-gray-600 dark:text-gray-400"
            />
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

      {/* User Avatar Dropdown */}
      <Dropdown
        align="right"
        width="w-60"
        trigger={
          <Avatar className="h-8 w-8 ring-2 ring-gray-300 dark:ring-gray-700 rounded-full cursor-pointer hover:ring-primary transition-colors">
            {testUser.image ? (
              <AvatarImage src={testUser.image} alt={userName} />
            ) : null}
            <AvatarFallback className="bg-primary text-white rounded-full">
              {userInitials}
            </AvatarFallback>
          </Avatar>
        }
      >
        <div className="px-4 py-3 text-sm text-gray-900 dark:text-gray-200">
          <div className="font-medium">{userName}</div>
          <div className="truncate text-gray-500 dark:text-gray-400">
            {user.email}
          </div>
        </div>
        <DropdownSeparator />
        <DropdownItem
          onClick={handleSettings}
          icon={<IconSettings size={16} />}
        >
          {t('nav.settings')}
        </DropdownItem>
        <DropdownSeparator />
        <DropdownItem onClick={() => logout()} icon={<IconLogout size={16} />}>
          {t('nav.logout')}
        </DropdownItem>
      </Dropdown>
    </div>
  );
}
