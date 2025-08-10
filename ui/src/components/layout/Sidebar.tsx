import { SeasLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';
import {
  Dropdown,
  DropdownItem,
  DropdownSeparator,
} from '@/components/ui/dropdown';
import { useLanguage } from '@/hooks/useLanguage';
import {
  IconChevronLeft,
  IconDots,
  IconEdit,
  IconMessage,
  IconPin,
  IconPlus,
  IconSearch,
  IconTrash,
} from '@tabler/icons-react';
import React, { useState } from 'react';

interface SidebarProps {
  onNewChat: () => void;
}

interface ChatItem {
  id: string;
  label: string;
}

interface SidebarHeaderProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

interface ActionButtonsProps {
  isCollapsed: boolean;
  onNewChat: () => void;
}

interface ChatItemProps {
  item: ChatItem;
  isPinned?: boolean;
}

interface ChatSectionProps {
  title: string;
  items: ChatItem[];
  isPinned?: boolean;
}

const historyItems: ChatItem[] = [
  { id: 'new-project-1', label: 'New Project' },
  { id: 'pricing-section-1', label: 'Pricing Section' },
  { id: 'design-guidelines-1', label: 'Design Guidelines' },
  { id: 'design-brief-1', label: 'Design Brief' },
  { id: 'marketing-1', label: 'Marketing' },
  { id: 'long-title-1', label: 'A very long title and it should be clipped' },
  { id: 'new-project-2', label: 'New Project' },
  { id: 'pricing-section-2', label: 'Pricing Section' },
  { id: 'design-guidelines-2', label: 'Design Guidelines' },
  { id: 'design-brief-2', label: 'Design Brief' },
  { id: 'marketing-2', label: 'Marketing' },
  { id: 'long-title-2', label: 'A very long title and it should be clipped' },
  { id: 'new-project-3', label: 'New Project' },
  { id: 'pricing-section-3', label: 'Pricing Section' },
  { id: 'design-guidelines-3', label: 'Design Guidelines' },
  { id: 'design-brief-3', label: 'Design Brief' },
];

const pinnedItems: ChatItem[] = [
  { id: 'important-meeting', label: 'Important Meeting Notes' },
  { id: 'project-specs', label: 'Project Specifications Specifications' },
];

const SidebarHeader: React.FC<SidebarHeaderProps> = ({
  isCollapsed,
  onToggle,
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex items-center justify-between p-4">
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={isCollapsed ? onToggle : undefined}
          className={`h-6 w-6 rounded-md text-primary hover:text-primary/80 ${isCollapsed ? 'cursor-pointer' : 'cursor-default'}`}
          title={isCollapsed ? t('sidebar.openSidebar') : 'SEAS'}
        >
          <SeasLogo size={32} className="text-primary" />
        </Button>
        {!isCollapsed && (
          <span className="text-lg font-semibold text-primary">SEAS</span>
        )}
      </div>
      {!isCollapsed && (
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className="h-6 w-6 cursor-pointer rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label={t('sidebar.collapseSidebar')}
          title={t('sidebar.collapseSidebar')}
        >
          <IconChevronLeft size={20} />
        </Button>
      )}
    </div>
  );
};

const ActionButtons: React.FC<ActionButtonsProps> = ({
  isCollapsed,
  onNewChat,
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col gap-2 p-2 mb-4">
      {!isCollapsed ? (
        <>
          <Button
            onClick={onNewChat}
            variant="ghost"
            className="flex w-full items-center justify-start gap-2 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl px-2 py-1 cursor-pointer"
          >
            <IconMessage size={16} />
            <span>{t('sidebar.newChat')}</span>
          </Button>
          <Button
            variant="ghost"
            className="flex w-full items-center justify-start gap-2 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl px-2 py-1 cursor-pointer"
          >
            <IconSearch size={16} />
            <span>{t('common.search')}</span>
          </Button>
        </>
      ) : (
        <>
          <Button
            onClick={onNewChat}
            variant="ghost"
            size="icon"
            className="rounded-lg text-gray-700 dark:text-gray-300 cursor-pointer"
            title={t('sidebar.newChat')}
          >
            <IconPlus size={16} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-lg text-gray-700 dark:text-gray-300 cursor-pointer"
            title={t('common.search')}
          >
            <IconSearch size={16} />
          </Button>
        </>
      )}
    </div>
  );
};

const ChatItemComponent: React.FC<ChatItemProps> = ({
  item,
  isPinned = false,
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex w-full items-center justify-between rounded-xl px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 group cursor-pointer relative">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {isPinned && (
          <IconPin
            size={14}
            className="text-gray-500 dark:text-gray-400 flex-shrink-0"
          />
        )}
        <button
          type="button"
          className="truncate text-left cursor-pointer min-w-0"
        >
          {item.label}
        </button>
      </div>
      <Dropdown
        trigger={
          <button
            type="button"
            className="p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 transition-opacity cursor-pointer flex-shrink-0"
          >
            <IconDots size={16} />
          </button>
        }
        align="left"
        width="w-40"
        offsetX={-128}
      >
        <DropdownItem icon={<IconEdit size={16} />}>
          {t('sidebar.rename')}
        </DropdownItem>
        <DropdownItem icon={<IconPin size={16} />}>
          {isPinned ? t('sidebar.unpinSession') : t('sidebar.pinSession')}
        </DropdownItem>
        <DropdownSeparator />
        <DropdownItem icon={<IconTrash size={16} />} danger>
          {t('sidebar.delete')}
        </DropdownItem>
      </Dropdown>
    </div>
  );
};

const ChatSection: React.FC<ChatSectionProps> = ({
  title,
  items,
  isPinned = false,
}) => (
  <div className="pl-2 pr-3 py-4 border-t border-gray-200">
    <div className="mb-2 px-2 text-xs font-medium text-gray-500 dark:text-gray-400">
      {title}
    </div>
    <div>
      {items.map((item) => (
        <ChatItemComponent key={item.id} item={item} isPinned={isPinned} />
      ))}
    </div>
  </div>
);

export const Sidebar: React.FC<SidebarProps> = ({ onNewChat }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { t } = useLanguage();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div
      className={`flex h-full flex-col bg-gray-50 dark:bg-gray-900 transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-64'}`}
    >
      <SidebarHeader isCollapsed={isCollapsed} onToggle={toggleSidebar} />

      <ActionButtons isCollapsed={isCollapsed} onNewChat={onNewChat} />

      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto min-h-0">
          {/* Pinned Section */}
          {pinnedItems.length > 0 && (
            <ChatSection
              title={t('sidebar.pinned')}
              items={pinnedItems}
              isPinned={true}
            />
          )}

          {/* History Section */}
          <ChatSection
            title={t('sidebar.history')}
            items={historyItems}
            isPinned={false}
          />

          {/* Bottom padding space */}
          <div className="p-1"></div>
        </div>
      )}
    </div>
  );
};
