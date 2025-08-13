import { ChatsService } from '@/client';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { UserControls } from '@/components/chat/UserControls';
import { Sidebar } from '@/components/layout/Sidebar';
import { Loading } from '@/components/ui/loading';
import useAuth from '@/hooks/useAuth';
import { useChatSessions } from '@/hooks/useChatSessions';
import { useLanguage } from '@/hooks/useLanguage';
import { useEffect, useState } from 'react';

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
  const [hasAutoLoaded, setHasAutoLoaded] = useState(false);
  const [isCreatingNewChat, setIsCreatingNewChat] = useState(false);

  // Auto-load the most recent session on startup
  useEffect(() => {
    if (
      !isLoadingSessions &&
      rawSessions.length > 0 &&
      !hasAutoLoaded &&
      !currentSessionId
    ) {
      // Filter sessions that have a firstMessage (non-empty sessions)
      const nonEmptySessions = rawSessions.filter(
        (session) => session.session_metadata?.firstMessage,
      );

      if (nonEmptySessions.length > 0) {
        // Sort non-empty sessions by created date
        const sortedSessions = [...nonEmptySessions].sort((a, b) => {
          const dateA = new Date(a.created_at);
          const dateB = new Date(b.created_at);
          return dateB.getTime() - dateA.getTime(); // Most recent first
        });

        setCurrentSessionId(sortedSessions[0].id);
        setHasAutoLoaded(true);
      } else {
        // If no non-empty sessions exist, auto-load the most recent session (even if empty)
        // This handles the case where user just logged in and only has the auto-created empty session
        const sortedSessions = [...rawSessions].sort((a, b) => {
          const dateA = new Date(a.created_at);
          const dateB = new Date(b.created_at);
          return dateB.getTime() - dateA.getTime(); // Most recent first
        });

        if (sortedSessions.length > 0) {
          setCurrentSessionId(sortedSessions[0].id);
          setHasAutoLoaded(true);
        }
      }
    }
  }, [rawSessions, isLoadingSessions, hasAutoLoaded, currentSessionId]);

  const isMostRecentSessionEmpty = async (): Promise<boolean> => {
    try {
      const latestSession = await ChatsService.getLatestChatSession();

      const response = await ChatsService.getChatMessages({
        chatSessionId: latestSession.id,
      });
      const messages = Array.isArray(response) ? response : [];

      return messages.length === 0;
    } catch (error: any) {
      // Handle 404 error when user has no chat sessions
      if (error?.status === 404) {
        return false;
      }

      console.error('Error checking if latest session is empty:', error);
      return false;
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
      // Check if the most recent session is empty before creating a new one
      const isRecentEmpty = await isMostRecentSessionEmpty();

      if (isRecentEmpty) {
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
