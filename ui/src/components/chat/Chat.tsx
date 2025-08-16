import { ChatsService } from '@/client';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { UserControls } from '@/components/chat/UserControls';
import { Sidebar } from '@/components/layout/Sidebar';
import { Loading } from '@/components/ui/loading';
import { LOCAL_STORAGE_KEYS } from '@/constants/localStorageKeys';
import useAuth from '@/hooks/useAuth';
import { useChatSessions } from '@/hooks/useChatSessions';
import { useLanguage } from '@/hooks/useLanguage';
import { IconMenu2, IconPlus } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

// Utility functions for session persistence
const saveSelectedSessionId = (sessionId: string | undefined) => {
  if (sessionId) {
    localStorage.setItem(LOCAL_STORAGE_KEYS.SELECTED_SESSION_ID, sessionId);
  } else {
    localStorage.removeItem(LOCAL_STORAGE_KEYS.SELECTED_SESSION_ID);
  }
};

const getSelectedSessionId = (): string | null => {
  return localStorage.getItem(LOCAL_STORAGE_KEYS.SELECTED_SESSION_ID);
};

export function Chat() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const {
    rawSessions,
    createSession,
    updateSessionWithFirstMessage,
    isLoading: isLoadingSessions,
  } = useChatSessions();
  const [currentSessionId, setCurrentSessionId] = useState<
    string | undefined
  >();
  const [isCreatingNewChat, setIsCreatingNewChat] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Auto-load the previously selected session on startup
  useEffect(() => {
    if (!isLoadingSessions && rawSessions.length > 0 && !currentSessionId) {
      // Try to restore the previously selected session
      const savedSessionId = getSelectedSessionId();

      // Check if the saved session still exists
      const savedSessionExists =
        savedSessionId &&
        rawSessions.some((session) => session.id === savedSessionId);

      if (savedSessionExists) {
        // Restore the previously selected session
        setCurrentSessionId(savedSessionId);
      } else {
        // If no valid saved session, load the most recent session as fallback
        const sortedSessions = [...rawSessions].sort((a, b) => {
          const dateA = new Date(a.created_at);
          const dateB = new Date(b.created_at);
          return dateB.getTime() - dateA.getTime(); // Most recent first
        });

        if (sortedSessions.length > 0) {
          setCurrentSessionId(sortedSessions[0].id);
        }
      }
    }
  }, [rawSessions, isLoadingSessions, currentSessionId]);

  // Save selected session ID to localStorage whenever it changes
  useEffect(() => {
    // Only save when we have a valid session ID
    // Don't clear localStorage when currentSessionId is undefined during initialization
    if (currentSessionId) {
      saveSelectedSessionId(currentSessionId);
    }
  }, [currentSessionId]);

  const checkLatestSession = async (): Promise<{
    isEmpty: boolean;
    session: any | null;
  }> => {
    try {
      const latestSession = await ChatsService.getLatestChatSession();

      const response = await ChatsService.getChatMessages({
        chatSessionId: latestSession.id,
      });
      const messages = Array.isArray(response) ? response : [];

      return {
        isEmpty: messages.length === 0,
        session: latestSession,
      };
    } catch (error: any) {
      // Handle 404 error when user has no chat sessions
      if (error?.status === 404) {
        return { isEmpty: false, session: null };
      }

      console.error('Error checking latest session:', error);
      return { isEmpty: false, session: null };
    }
  };

  const handleNewChat = async () => {
    // Prevent double creation
    if (isCreatingNewChat) {
      return;
    }

    // Set the flag immediately to prevent race conditions
    setIsCreatingNewChat(true);

    try {
      // Check if the latest session is empty before creating a new one
      const { isEmpty: isLatestEmpty, session: latestSession } =
        await checkLatestSession();

      if (isLatestEmpty && latestSession) {
        // If latest session is already empty, switch to it instead of creating new one
        setCurrentSessionId(latestSession.id);
        return;
      }

      // Create a new session with empty metadata initially
      const newSession = await createSession({ session_metadata: {} });
      setCurrentSessionId(newSession.id);
    } catch (error) {
      console.error('Error in handleNewChat:', error);
      setCurrentSessionId(undefined);
    } finally {
      setIsCreatingNewChat(false);
    }
  };

  const handleSelectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
  };

  // Simple first message handler - just update metadata for existing sessions
  const handleFirstMessage = async (message: string): Promise<void> => {
    if (currentSessionId && message.trim()) {
      try {
        await updateSessionWithFirstMessage(currentSessionId, message);
      } catch (error) {
        console.error('Failed to update session with first message:', error);
      }
    }
  };

  if (!user) {
    return <Loading message={t('common.loading')} />;
  }

  // Show loading while fetching sessions on initial load
  if (isLoadingSessions) {
    return <Loading message={t('chat.loadingSessions')} />;
  }

  const userName = user.full_name || user.email || 'User';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-gray-950 relative">
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 h-12 bg-white/80 dark:bg-gray-950/80 backdrop-blur border-b border-gray-200 dark:border-gray-800 flex items-center px-3">
        <div className="flex items-center gap-2">
          <button
            aria-label="Open sidebar"
            className="h-9 w-9 flex items-center justify-center rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
            onClick={() => setIsMobileSidebarOpen(true)}
          >
            <IconMenu2 size={20} />
          </button>
          <button
            aria-label={t('sidebar.newChat')}
            title={t('sidebar.newChat')}
            className="h-9 w-9 flex items-center justify-center rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
            onClick={handleNewChat}
            disabled={isCreatingNewChat}
          >
            {isCreatingNewChat ? (
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-gray-300 border-t-gray-600" />
            ) : (
              <IconPlus size={20} />
            )}
          </button>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <span className="text-lg font-semibold text-primary">SEAS</span>
        </div>
        <div className="flex items-center gap-3">
          <UserControls inline />
        </div>
      </div>

      {/* Backdrop for mobile sidebar */}
      {isMobileSidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-20 bg-black/40"
          onClick={() => setIsMobileSidebarOpen(false)}
        />
      )}

      {/* Off-canvas mobile sidebar */}
      <div
        className={`md:hidden fixed top-0 left-0 z-30 h-full transform transition-transform duration-300 ${
          isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="w-64 h-full bg-gray-50 dark:bg-gray-900 shadow-xl">
          <Sidebar
            onNewChat={handleNewChat}
            onSelectSession={(id) => {
              setIsMobileSidebarOpen(false);
              handleSelectSession(id);
            }}
            isCreatingNewChat={isCreatingNewChat}
            currentSessionId={currentSessionId}
            forceExpanded
            onRequestClose={() => setIsMobileSidebarOpen(false)}
          />
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar
          onNewChat={handleNewChat}
          onSelectSession={handleSelectSession}
          isCreatingNewChat={isCreatingNewChat}
          currentSessionId={currentSessionId}
        />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col h-full pt-12 md:pt-0">
        {/* Top-right controls on desktop */}
        <div className="hidden md:block">
          <UserControls />
        </div>

        {/* Chat container */}
        <div className="flex-1 min-h-0">
          <ChatContainer
            userName={userName.split(' ')[0]}
            sessionId={currentSessionId}
            onFirstMessage={handleFirstMessage}
          />
        </div>
      </div>
    </div>
  );
}
