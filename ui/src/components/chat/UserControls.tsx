import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Dropdown,
  DropdownItem,
  DropdownSeparator,
} from '@/components/ui/dropdown';
import { LanguageSelector } from '@/components/ui/language-selector';
import useAuth from '@/hooks/useAuth';
import { useLanguage } from '@/hooks/useLanguage';
import { IconLogout, IconSettings } from '@tabler/icons-react';
import { useState } from 'react';

export function UserControls() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const [testUser] = useState({
    id: '1',
    name: 'Test user',
    image: undefined,
  });

  const handleSettings = () => {
    console.log('Settings clicked');
    // Implementation would open settings panel
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
      <LanguageSelector />

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
