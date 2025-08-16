import { ChatsService } from '@/client';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { UserControls } from '@/components/chat/UserControls';
import { Sidebar } from '@/components/layout/Sidebar';
import { Loading } from '@/components/ui/loading';
import { LOCAL_STORAGE_KEYS } from '@/constants/localStorageKeys';
import useAuth from '@/hooks/useAuth';
import { useChatSessions } from '@/hooks/useChatSessions';
import { useLanguage } from '@/hooks/useLanguage';
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
      {/* User Controls (Language Toggle + User Avatar) in top right corner */}
      <UserControls />

      {/* Sidebar */}
      <Sidebar
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        isCreatingNewChat={isCreatingNewChat}
        currentSessionId={currentSessionId}
      />

      {/* Main content */}
      <div className="flex flex-1 flex-col h-full">
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
