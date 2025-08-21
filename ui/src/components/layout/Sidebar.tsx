import { SeasLogo } from '@/components/icons';
import { SidebarFooter } from '@/components/layout/SidebarFooter';
import { Button } from '@/components/ui/button';
import { ConfirmDialog } from '@/components/ui/dialog';
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
  IconChevronsRight,
  IconDots,
  IconEdit,
  IconMessage,
  IconPin,
  IconPlus,
  IconSearch,
  IconTrash,
  IconX,
} from '@tabler/icons-react';
import React, { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

interface SidebarProps {
  onNewChat: () => void;
  onSelectSession?: (sessionId: string) => void;
  isCreatingNewChat?: boolean;
  currentSessionId?: string;
  forceExpanded?: boolean;
  onRequestClose?: () => void;
}

interface DialogState {
  type: 'delete' | null;
  sessionId: string | null;
  sessionName: string | null;
}

interface SidebarHeaderProps {
  isCollapsed: boolean;
  onToggle: () => void;
  onClose?: () => void;
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
  onRename: (sessionId: string, newName: string) => void;
  onPin: (sessionId: string, isPinned: boolean) => void;
  onDelete: (sessionId: string, sessionName: string) => void;
  isRenaming?: boolean;
  onStartRename: (sessionId: string) => void;
  onCancelRename: () => void;
}

interface ChatSectionProps {
  title: string;
  items: ChatSessionItem[];
  isPinned?: boolean;
  isLoading?: boolean;
  onSelectSession?: (sessionId: string) => void;
  currentSessionId?: string;
  onRename: (sessionId: string, newName: string) => void;
  onPin: (sessionId: string, isPinned: boolean) => void;
  onDelete: (sessionId: string, sessionName: string) => void;
  renamingSessionId?: string;
  onStartRename: (sessionId: string) => void;
  onCancelRename: () => void;
}

const SidebarHeader: React.FC<SidebarHeaderProps> = ({
  isCollapsed,
  onToggle,
  onClose,
}) => {
  const { t } = useLanguage();
  const handleLogoClick = () => {
    window.location.href = '/';
  };

  return (
    <div className="flex items-center justify-between p-4">
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleLogoClick}
          className={`h-6 w-6 rounded-md text-primary hover:text-primary/80 cursor-pointer`}
          title={'SEAS'}
        >
          <SeasLogo size={32} className="text-primary" />
        </Button>
        {!isCollapsed && (
          <button
            type="button"
            onClick={handleLogoClick}
            className="text-lg font-semibold text-primary cursor-pointer"
            title="SEAS"
          >
            SEAS
          </button>
        )}
      </div>
      {!isCollapsed && (
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose ?? onToggle}
          className="h-6 w-6 cursor-pointer rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label={
            onClose ? t('common.close') : t('sidebar.collapseSidebar')
          }
          title={onClose ? t('common.close') : t('sidebar.collapseSidebar')}
        >
          {onClose ? <IconX size={20} /> : <IconChevronLeft size={20} />}
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
    <div className="flex flex-col gap-1 p-2 mb-2">
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
  onRename,
  onPin,
  onDelete,
  isRenaming = false,
  onStartRename,
  onCancelRename,
}) => {
  const { t } = useLanguage();
  const [editingName, setEditingName] = useState(item.label);

  // Reset editing name when item changes or rename mode changes
  useEffect(() => {
    setEditingName(item.label);
  }, [item.label, isRenaming]);

  const handleClick = () => {
    if (!isRenaming) {
      onSelect?.(item.id);
    }
  };

  const handleStartRename = () => {
    onStartRename(item.id);
  };

  const handleRenameSubmit = () => {
    if (editingName.trim() && editingName.trim() !== item.label) {
      onRename(item.id, editingName.trim());
    } else {
      onCancelRename();
    }
  };

  const handleRenameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setEditingName(item.label);
      onCancelRename();
    }
  };

  const handleRenameBlur = () => {
    handleRenameSubmit();
  };

  const handlePin = () => {
    onPin(item.id, !isPinned);
  };

  const handleDelete = () => {
    onDelete(item.id, item.label);
  };

  const handleDropdownClick = (e: React.MouseEvent) => {
    e.stopPropagation();
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
        {isRenaming ? (
          <input
            type="text"
            value={editingName}
            onChange={(e) => setEditingName(e.target.value)}
            onKeyDown={handleRenameKeyDown}
            onBlur={handleRenameBlur}
            className="flex-1 bg-transparent border-none outline-none text-sm min-w-0 px-1 py-0.5 rounded border border-primary focus:border-primary"
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <button
            type="button"
            className="truncate text-left cursor-pointer min-w-0 flex-1"
          >
            {item.label}
          </button>
        )}
      </div>
      {!isRenaming && (
        <div onClick={handleDropdownClick}>
          <Dropdown
            trigger={
              <button
                type="button"
                className="p-1 rounded-md opacity-100 md:opacity-0 md:group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 transition-opacity cursor-pointer flex-shrink-0"
              >
                <IconDots size={16} />
              </button>
            }
            align="left"
            width="w-40"
            offsetX={-128}
          >
            <DropdownItem
              icon={<IconEdit size={16} />}
              onClick={handleStartRename}
            >
              {t('sidebar.rename')}
            </DropdownItem>
            <DropdownItem icon={<IconPin size={16} />} onClick={handlePin}>
              {isPinned ? t('sidebar.unpinSession') : t('sidebar.pinSession')}
            </DropdownItem>
            <DropdownSeparator />
            <DropdownItem
              icon={<IconTrash size={16} />}
              danger
              onClick={handleDelete}
            >
              {t('sidebar.delete')}
            </DropdownItem>
          </Dropdown>
        </div>
      )}
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
  onRename,
  onPin,
  onDelete,
  renamingSessionId,
  onStartRename,
  onCancelRename,
}) => {
  if (isLoading) {
    return (
      <div className="pl-2 pr-3 py-2 border-t border-gray-200">
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
    <div className="pl-2 pr-3 py-2 border-t border-gray-200">
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
            onRename={onRename}
            onPin={onPin}
            onDelete={onDelete}
            isRenaming={renamingSessionId === item.id}
            onStartRename={onStartRename}
            onCancelRename={onCancelRename}
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
  forceExpanded,
  onRequestClose,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(
    null,
  );
  const [dialogState, setDialogState] = useState<DialogState>({
    type: null,
    sessionId: null,
    sessionName: null,
  });
  const { t } = useLanguage();
  const reportIssueUrl = import.meta.env.VITE_REPORT_ISSUE_LINK as
    | string
    | undefined;

  // Collapse sidebar by default on mobile screens
  useEffect(() => {
    const isMobile = window.matchMedia('(max-width: 767px)').matches;
    if (isMobile) {
      setIsCollapsed(true);
    }
  }, []);

  const effectiveCollapsed = forceExpanded ? false : isCollapsed;

  const {
    pinnedSessions,
    regularSessions,
    isLoading,
    isError,
    isCreating,
    renameSession,
    togglePinSession,
    deleteSession,
    isDeletingSession,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useChatSessions();

  // Infinite scroll: observe a sentinel at the bottom of the scroll area
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const userHasScrolledRef = useRef(false);

  useEffect(() => {
    if (!scrollContainerRef.current || !sentinelRef.current) return;
    const root = scrollContainerRef.current;
    const sentinel = sentinelRef.current;

    // Track whether user has scrolled to prevent immediate prefetching
    const onScroll = () => {
      if (root.scrollTop > 0) {
        userHasScrolledRef.current = true;
      }
    };
    root.addEventListener('scroll', onScroll, { passive: true });

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (
          entry.isIntersecting &&
          userHasScrolledRef.current &&
          hasNextPage &&
          !isFetchingNextPage
        ) {
          fetchNextPage();
        }
      },
      { root, rootMargin: '0px', threshold: 0.01 },
    );
    observer.observe(sentinel);
    return () => {
      observer.disconnect();
      root.removeEventListener('scroll', onScroll);
    };
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, effectiveCollapsed]);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleRetry = () => {
    // Force a page reload as a simple retry mechanism
    window.location.reload();
  };

  const handleStartRename = (sessionId: string) => {
    setRenamingSessionId(sessionId);
  };

  const handleCancelRename = () => {
    setRenamingSessionId(null);
  };

  const openDeleteDialog = (sessionId: string, sessionName: string) => {
    setDialogState({
      type: 'delete',
      sessionId,
      sessionName,
    });
  };

  const closeDialog = () => {
    setDialogState({
      type: null,
      sessionId: null,
      sessionName: null,
    });
  };

  const handleRename = async (sessionId: string, newName: string) => {
    try {
      await renameSession({
        sessionId,
        newTitle: newName,
      });
      toast.success(t('messages.success'));
      setRenamingSessionId(null);
    } catch (error) {
      console.error('Failed to rename session:', error);
      toast.error('Failed to rename session');
    }
  };

  const handlePin = async (sessionId: string, isPinned: boolean) => {
    try {
      await togglePinSession({ sessionId, isPinned });
      toast.success(
        isPinned ? t('sidebar.sessionPinned') : t('sidebar.sessionUnpinned'),
      );
    } catch (error) {
      console.error('Failed to toggle pin session:', error);
      toast.error('Failed to update session');
    }
  };

  const handleDelete = async () => {
    if (!dialogState.sessionId) return;

    try {
      await deleteSession({ sessionId: dialogState.sessionId });
      toast.success(t('messages.success'));
      closeDialog();

      // If the deleted session was the current one, clear selection
      if (currentSessionId === dialogState.sessionId) {
        onSelectSession?.('');
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      toast.error('Delete functionality not available yet');
      closeDialog();
    }
  };

  const handleNewChatClick = () => {
    onNewChat();
    if (onRequestClose) {
      onRequestClose();
    }
  };

  return (
    <div
      className={`flex h-full flex-col bg-gray-50 dark:bg-gray-900 transition-all duration-300 ${effectiveCollapsed ? 'w-16' : 'w-64'}`}
    >
      <SidebarHeader
        isCollapsed={effectiveCollapsed}
        onToggle={toggleSidebar}
        onClose={onRequestClose}
      />

      {effectiveCollapsed && (
        <div className="px-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="rounded-lg text-gray-700 dark:text-gray-300 cursor-pointer"
            aria-label={t('sidebar.expandSidebar')}
            title={t('sidebar.expandSidebar')}
          >
            <IconChevronsRight size={20} />
          </Button>
        </div>
      )}

      <ActionButtons
        isCollapsed={effectiveCollapsed}
        onNewChat={handleNewChatClick}
        isCreatingSession={isCreating}
        isCreatingNewChat={isCreatingNewChat}
      />

      {!effectiveCollapsed && (
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-y-auto scrollbar-hide"
        >
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
                onRename={handleRename}
                onPin={handlePin}
                onDelete={openDeleteDialog}
                renamingSessionId={renamingSessionId || undefined}
                onStartRename={handleStartRename}
                onCancelRename={handleCancelRename}
              />

              {/* History Section */}
              <ChatSection
                title={t('sidebar.history')}
                items={regularSessions}
                isPinned={false}
                isLoading={isLoading}
                onSelectSession={onSelectSession}
                currentSessionId={currentSessionId}
                onRename={handleRename}
                onPin={handlePin}
                onDelete={openDeleteDialog}
                renamingSessionId={renamingSessionId || undefined}
                onStartRename={handleStartRename}
                onCancelRename={handleCancelRename}
              />
            </>
          )}

          {/* Bottom padding space */}
          <div className="p-1"></div>
          {/* Infinite scroll sentinel and loader */}
          {hasNextPage && <div ref={sentinelRef} />}
          {isFetchingNextPage && (
            <div className="pl-2 pr-3 py-2 border-t border-gray-200">
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
          )}
        </div>
      )}

      <SidebarFooter
        isCollapsed={effectiveCollapsed}
        reportIssueUrl={reportIssueUrl}
      />

      {/* Delete Confirmation Dialog - Keep only this dialog */}
      <ConfirmDialog
        open={dialogState.type === 'delete'}
        onClose={closeDialog}
        onConfirm={handleDelete}
        title={t('sidebar.deleteSession')}
        message={t('sidebar.deleteSessionConfirm', {
          sessionName: dialogState.sessionName,
        })}
        confirmText={t('sidebar.delete')}
        confirmButtonVariant="primary"
        isLoading={isDeletingSession}
      />
    </div>
  );
};
