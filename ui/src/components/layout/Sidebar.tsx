import {
  ChatIcon,
  EllipsisIcon,
  LeftDoubleArrowIcon,
  PlusIcon,
  SearchIcon,
} from '@/components/icons';
import { Button } from '@/components/ui/button';
import {
  Dropdown,
  DropdownItem,
  DropdownSeparator,
} from '@/components/ui/dropdown';
import React, { useState } from 'react';

interface SidebarProps {
  onNewChat: () => void;
}

const historyItems = [
  { id: 'new-project', label: 'New Project' },
  { id: 'pricing-section', label: 'Pricing Section' },
  { id: 'design-guidelines', label: 'Design Guidelines' },
  { id: 'design-brief', label: 'Design Brief' },
  { id: 'marketing', label: 'Marketing' },
  { id: 'long-title', label: 'A very long title and it should be clipped' },
];

export const Sidebar: React.FC<SidebarProps> = ({ onNewChat }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div
      className={`flex h-full flex-col bg-gray-50 dark:bg-gray-900 transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-64'}`}
    >
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={isCollapsed ? toggleSidebar : undefined}
            className={`h-6 w-6 rounded-md text-primary hover:text-primary/80 ${isCollapsed ? 'cursor-pointer' : 'cursor-default'}`}
            title={isCollapsed ? 'Open Sidebar' : 'SEAS'}
          >
            <ChatIcon className="h-5 w-5" />
          </Button>
          {!isCollapsed && (
            <span className="text-lg font-semibold text-primary">SEAS</span>
          )}
        </div>
        {!isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="h-6 w-6 cursor-pointer rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            aria-label="Collapse Sidebar"
            title="Collapse Sidebar"
          >
            <LeftDoubleArrowIcon size={20} />
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-2 p-2 mb-4">
        {!isCollapsed ? (
          <>
            <Button
              onClick={onNewChat}
              variant="ghost"
              className="flex w-full items-center justify-start gap-2 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl px-2 py-1 cursor-pointer"
            >
              <ChatIcon size={16} />
              <span>New Chat</span>
            </Button>
            <Button
              variant="ghost"
              className="flex w-full items-center justify-start gap-2 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl px-2 py-1 cursor-pointer"
            >
              <SearchIcon size={16} />
              <span>Search Chats</span>
            </Button>
          </>
        ) : (
          <>
            <Button
              onClick={onNewChat}
              variant="ghost"
              size="icon"
              className="rounded-lg text-gray-700 dark:text-gray-300 cursor-pointer"
              title="New Chat"
            >
              <PlusIcon size={16} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="rounded-lg text-gray-700 dark:text-gray-300 cursor-pointer"
              title="Search Chats"
            >
              <SearchIcon size={16} />
            </Button>
          </>
        )}
      </div>

      {!isCollapsed && (
        <div className="pl-2 pr-3 py-4 border-t border-gray-200">
          <div className="mb-2 px-2 text-xs font-medium text-gray-500 dark:text-gray-400">
            History
          </div>
          <div className="space-y-1">
            {historyItems.map((item) => (
              <div
                key={item.id}
                className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 group cursor-pointer relative"
              >
                <button className="truncate text-left cursor-pointer">
                  {item.label}
                </button>
                <Dropdown
                  trigger={
                    <button className="p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 transition-opacity cursor-pointer">
                      <EllipsisIcon size={16} />
                    </button>
                  }
                  align="left"
                  width="w-40"
                  offsetX={0}
                >
                  <DropdownItem>Rename</DropdownItem>
                  <DropdownItem>Add to favorites</DropdownItem>
                  <DropdownSeparator />
                  <DropdownItem danger>Delete</DropdownItem>
                </Dropdown>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom padding space */}
      <div className="mt-auto p-4"></div>
    </div>
  );
};
