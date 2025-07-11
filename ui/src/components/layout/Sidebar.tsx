import React from 'react';
import { ChatIcon, PlusIcon, SettingsIcon } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface SidebarProps {
  onNewChat: () => void;
  onSettingsClick: () => void;
  userName: string;
  userAvatar?: string;
}

const historyItems = [
  { id: 'new-project', label: 'New Project' },
  { id: 'pricing-section', label: 'Pricing Section' },
  { id: 'design-guidelines', label: 'Design Guidelines' },
  { id: 'design-brief', label: 'Design Brief' },
  { id: 'marketing', label: 'Marketing' },
];

export const Sidebar: React.FC<SidebarProps> = ({
  onNewChat,
  onSettingsClick,
  userName,
  userAvatar,
}) => {
  const userInitials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  return (
    <div className="flex h-full w-64 flex-col bg-gray-50 dark:bg-gray-900">
      <div className="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <ChatIcon className="h-5 w-5 text-primary" />
          <span className="text-lg font-semibold text-primary">SEAS</span>
        </div>
      </div>

      <div className="flex flex-col gap-2 p-2">
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="flex-1 justify-start gap-2 rounded-lg text-gray-700 dark:text-gray-300"
          >
            <ChatIcon size={16} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-lg text-gray-700 dark:text-gray-300"
          >
            <PlusIcon size={16} />
          </Button>
        </div>

        <Button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 bg-gray-900 dark:bg-gray-800 rounded-xl"
        >
          <ChatIcon size={16} />
          <span>New Chat</span>
        </Button>
      </div>

      <div className="px-2 py-4">
        <div className="mb-2 px-2 text-xs font-medium text-gray-500 dark:text-gray-400">
          History
        </div>
        <div className="space-y-1">
          {historyItems.map((item) => (
            <button
              key={item.id}
              className="flex w-full cursor-pointer items-center rounded-lg px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-auto flex items-center justify-between border-t border-gray-200 p-4 dark:border-gray-800">
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-gray-700 dark:text-gray-300"
          onClick={onSettingsClick}
        >
          <SettingsIcon size={16} className="mr-1" />
          Settings
        </Button>

        <Avatar className="h-8 w-8">
          {userAvatar ? <AvatarImage src={userAvatar} alt={userName} /> : null}
          <AvatarFallback className="bg-primary text-white">
            {userInitials}
          </AvatarFallback>
        </Avatar>
      </div>
    </div>
  );
};
