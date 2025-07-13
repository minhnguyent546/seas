import { ChatContainer } from '@/components/chat/ChatContainer';
import { LogoutIcon, SettingsIcon } from '@/components/icons';
import { Sidebar } from '@/components/layout/Sidebar';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Dropdown,
  DropdownItem,
  DropdownSeparator,
} from '@/components/ui/dropdown';
import { Loading } from '@/components/ui/loading';
import useAuth from '@/hooks/useAuth';
import { useState } from 'react';

export function Chat() {
  const { user, logout } = useAuth();
  const [testUser] = useState({
    id: '1',
    name: 'Test user',
    image: undefined,
  });

  const handleNewChat = () => {
    console.log('New chat created');
    // Implementation would reset the current chat or create a new one
  };

  const handleSettings = () => {
    console.log('Settings clicked');
    // Implementation would open settings panel
  };

  if (!user) {
    return <Loading message="Loading..." />;
  }

  const userName = user.full_name || user.email || 'User';
  const userInitials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-gray-950 relative">
      {/* User Avatar in top right corner with dropdown */}
      <div className="absolute top-4 right-4 z-10">
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
            icon={<SettingsIcon size={16} />}
          >
            Settings
          </DropdownItem>
          <DropdownSeparator />
          <DropdownItem
            onClick={() => logout()}
            icon={<LogoutIcon size={16} />}
          >
            Sign out
          </DropdownItem>
        </Dropdown>
      </div>

      {/* Sidebar */}
      <Sidebar onNewChat={handleNewChat} />

      {/* Main content */}
      <div className="flex flex-1 flex-col h-full">
        {/* Chat container */}
        <div className="flex-1 min-h-0">
          <ChatContainer userName={userName.split(' ')[0]} />
        </div>
      </div>
    </div>
  );
}
