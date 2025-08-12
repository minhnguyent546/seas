import { SeasLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';
import {
  Dropdown,
  DropdownItem,
  DropdownSeparator,
} from '@/components/ui/dropdown';
import { useChatSessions, type ChatSessionItem } from '@/hooks/useChatSessions';
import { useLanguage } from '@/hooks/useLanguage';
import {
  IconAlertCircle,
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
  onSelectSession?: (sessionId: string) => void;
  isCreatingNewChat?: boolean;
  currentSessionId?: string;
}

interface SidebarHeaderProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

interface ActionButtonsProps {
  isCollapsed: boolean;
  onNewChat: () => void;
  isCreatingSession: boolean;
  isCreatingNewChat?: boolean;
}

interface ChatItemProps {
  item: ChatSessionItem;
  isPinned?: boolean;
  onSelect?: (sessionId: string) => void;
  isSelected?: boolean;
}

interface ChatSectionProps {
  title: string;
  items: ChatSessionItem[];
  isPinned?: boolean;
  isLoading?: boolean;
  onSelectSession?: (sessionId: string) => void;
  currentSessionId?: string;
}

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
  isCreatingSession,
  isCreatingNewChat,
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col gap-2 p-2 mb-4">
      {!isCollapsed ? (
        <>
          <Button
            onClick={onNewChat}
            variant="ghost"
            disabled={isCreatingSession || isCreatingNewChat}
            className="flex w-full items-center justify-start gap-2 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl px-2 py-1 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isCreatingSession || isCreatingNewChat ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-gray-600" />
            ) : (
              <IconMessage size={16} />
            )}
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
            disabled={isCreatingSession || isCreatingNewChat}
            className="rounded-lg text-gray-700 dark:text-gray-300 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            title={t('sidebar.newChat')}
          >
            {isCreatingSession || isCreatingNewChat ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-gray-600" />
            ) : (
              <IconPlus size={16} />
            )}
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
  onSelect,
  isSelected = false,
}) => {
  const { t } = useLanguage();

  const handleClick = () => {
    onSelect?.(item.id);
  };

  return (
    <div
      className={`flex w-full items-center justify-between rounded-xl px-2 py-1.5 text-sm group cursor-pointer relative transition-colors ${
        isSelected
          ? 'bg-primary/15 text-primary dark:bg-primary/25 dark:text-primary-light'
          : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
      }`}
      onClick={handleClick}
    >
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
  isLoading = false,
  onSelectSession,
  currentSessionId,
}) => {
  if (isLoading) {
    return (
      <div className="pl-2 pr-3 py-4 border-t border-gray-200">
        <div className="mb-2 px-2 text-xs font-medium text-gray-500 dark:text-gray-400">
          {title}
        </div>
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="animate-pulse flex items-center gap-2 px-2 py-1.5"
            >
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded flex-1"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="pl-2 pr-3 py-4 border-t border-gray-200">
      <div className="mb-2 px-2 text-xs font-medium text-gray-500 dark:text-gray-400">
        {title}
      </div>
      <div>
        {items.map((item) => (
          <ChatItemComponent
            key={item.id}
            item={item}
            isPinned={isPinned}
            onSelect={onSelectSession}
            isSelected={currentSessionId === item.id}
          />
        ))}
      </div>
    </div>
  );
};

const ErrorState: React.FC<{ onRetry: () => void }> = ({ onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center p-4 text-center">
      <IconAlertCircle size={32} className="text-red-500 mb-2" />
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
        Failed to load chat sessions
      </p>
      <Button onClick={onRetry} variant="ghost" size="sm" className="text-xs">
        Try again
      </Button>
    </div>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({
  onNewChat,
  onSelectSession,
  isCreatingNewChat,
  currentSessionId,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { t } = useLanguage();

  const { pinnedSessions, regularSessions, isLoading, isError, isCreating } =
    useChatSessions();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  // Remove the duplicate handleNewChat - use the prop from parent instead!
  // The parent Chat component has the proper empty session validation

  const handleRetry = () => {
    // Force a page reload as a simple retry mechanism
    window.location.reload();
  };

  return (
    <div
      className={`flex h-full flex-col bg-gray-50 dark:bg-gray-900 transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-64'}`}
    >
      <SidebarHeader isCollapsed={isCollapsed} onToggle={toggleSidebar} />

      <ActionButtons
        isCollapsed={isCollapsed}
        onNewChat={onNewChat}
        isCreatingSession={isCreating}
        isCreatingNewChat={isCreatingNewChat}
      />

      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto min-h-0">
          {isError ? (
            <ErrorState onRetry={handleRetry} />
          ) : (
            <>
              {/* Pinned Section */}
              <ChatSection
                title={t('sidebar.pinned')}
                items={pinnedSessions}
                isPinned={true}
                isLoading={isLoading}
                onSelectSession={onSelectSession}
                currentSessionId={currentSessionId}
              />

              {/* History Section */}
              <ChatSection
                title={t('sidebar.history')}
                items={regularSessions}
                isPinned={false}
                isLoading={isLoading}
                onSelectSession={onSelectSession}
                currentSessionId={currentSessionId}
              />
            </>
          )}

          {/* Bottom padding space */}
          <div className="p-1"></div>
        </div>
      )}
    </div>
  );
};
