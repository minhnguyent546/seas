import { ChatContainer } from '@/components/chat/ChatContainer';
import { Sidebar } from '@/components/layout/Sidebar';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Dropdown, DropdownItem } from '@/components/ui/dropdown';
import { Loading } from '@/components/ui/loading';
import useAuth from '@/hooks/useAuth';
import { useState } from 'react';

// Simple inline icons for the dropdown
const SettingsIcon = ({ size = 24, ...props }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const LogoutIcon = ({ size = 24, ...props }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

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
          <hr className="border-gray-200 dark:border-gray-700" />
          <DropdownItem
            onClick={handleSettings}
            icon={<SettingsIcon size={16} />}
          >
            Settings
          </DropdownItem>
          <hr className="border-gray-200 dark:border-gray-700" />
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
