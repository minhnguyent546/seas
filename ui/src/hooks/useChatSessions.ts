import {
  ChatsService,
  type ChatSessionCreate,
  type ChatSessionPublic,
} from '@/client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export const CHAT_QUERY_KEYS = {
  sessions: ['chatSessions'] as const,
  session: (id: string) => ['chatSession', id] as const,
} as const;

const getSessionTitle = (session: ChatSessionPublic): string => {
  const metadata = session.session_metadata;

  // Try to get title from various possible metadata fields
  if (metadata?.title && typeof metadata.title === 'string') {
    return metadata.title;
  }
  if (metadata?.name && typeof metadata.name === 'string') {
    return metadata.name;
  }

  // Try to get the first user message from metadata
  if (metadata?.firstMessage && typeof metadata.firstMessage === 'string') {
    // Truncate to first 50 characters and add ellipsis if needed
    const truncated =
      metadata.firstMessage.length > 50
        ? metadata.firstMessage.substring(0, 50).trim() + '...'
        : metadata.firstMessage.trim();

    return truncated || 'New Chat';
  }

  let date: Date;

  try {
    date = new Date(session.created_at);

    if (isNaN(date.getTime())) {
      date = new Date();
    }
  } catch (error) {
    date = new Date();
  }

  const timeString = date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  return `Chat ${timeString}`;
};

export interface ChatSessionItem {
  id: string;
  label: string;
  isPinned?: boolean;
}

export const useChatSessions = () => {
  const queryClient = useQueryClient();

  const sessionsQuery = useQuery({
    queryKey: CHAT_QUERY_KEYS.sessions,
    queryFn: async () => {
      try {
        const sessions = await ChatsService.getChatSessions();

        // If user has no sessions, automatically create one
        if (sessions.length === 0) {
          const newSession = await ChatsService.createChatSession({
            requestBody: { session_metadata: {} },
          });
          // Return the new session as an array
          return [newSession];
        }

        return sessions;
      } catch (error) {
        console.error('Failed to fetch chat sessions:', error);
        throw error;
      }
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
  });

  // Mutation to create a new chat session
  const createSessionMutation = useMutation({
    mutationFn: async (data?: ChatSessionCreate) => {
      return ChatsService.createChatSession({
        requestBody: data || { session_metadata: {} },
      });
    },
    onSuccess: () => {
      // Invalidate and refetch sessions when a new one is created
      queryClient.invalidateQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
    },
  });

  // Mutation to update a chat session (e.g., to add first message)
  const updateSessionMutation = useMutation({
    mutationFn: async ({
      sessionId,
      data,
    }: {
      sessionId: string;
      data: any;
    }) => {
      return ChatsService.updateChatSession({
        chatSessionId: sessionId,
        requestBody: data,
      });
    },
    onSuccess: () => {
      // Invalidate and refetch sessions when updated
      queryClient.invalidateQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
    },
  });

  // Mutation to rename a chat session
  const renameSessionMutation = useMutation({
    mutationFn: async ({
      sessionId,
      newTitle,
    }: {
      sessionId: string;
      newTitle: string;
    }) => {
      const session = sessionsQuery.data?.find((s) => s.id === sessionId);
      if (!session) {
        throw new Error('Session not found');
      }

      const updatedMetadata = {
        ...session.session_metadata,
        firstMessage: newTitle,
      };

      return ChatsService.updateChatSession({
        chatSessionId: sessionId,
        requestBody: { session_metadata: updatedMetadata },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
    },
  });

  // Mutation to pin/unpin a chat session
  const togglePinSessionMutation = useMutation({
    mutationFn: async ({
      sessionId,
      isPinned,
    }: {
      sessionId: string;
      isPinned: boolean;
    }) => {
      return ChatsService.updateChatSession({
        chatSessionId: sessionId,
        requestBody: { is_favorite: isPinned },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
    },
  });

  // Mutation for delete session
  const deleteSessionMutation = useMutation({
    mutationFn: async ({ sessionId }: { sessionId: string }) => {
      return ChatsService.deleteChatSession({
        chatSessionId: sessionId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
    },
  });

  // Transform sessions to the format expected by the Sidebar
  const transformedSessions: ChatSessionItem[] =
    sessionsQuery.data?.map((session) => ({
      id: session.id,
      label: getSessionTitle(session),
      isPinned: session.is_favorite,
    })) || [];

  // Filter out empty sessions (sessions without a firstMessage in metadata)
  const nonEmptySessions = transformedSessions.filter((session) => {
    const originalSession = sessionsQuery.data?.find(
      (s) => s.id === session.id,
    );
    if (!originalSession) return false;

    // Only show sessions that have a firstMessage in their metadata
    // This means the user has sent at least one message
    return originalSession.session_metadata?.firstMessage;
  });

  // Sort all sessions by updated_at (most recently active first)
  const sortedSessions = [...nonEmptySessions].sort((a, b) => {
    const sessionA = sessionsQuery.data?.find((s) => s.id === a.id);
    const sessionB = sessionsQuery.data?.find((s) => s.id === b.id);

    if (!sessionA || !sessionB) return 0;

    const dateA = new Date(sessionA.created_at);
    const dateB = new Date(sessionB.created_at);
    return dateB.getTime() - dateA.getTime();
  });

  const pinnedSessions = sortedSessions.filter((session) => session.isPinned);
  const regularSessions = sortedSessions.filter((session) => !session.isPinned);

  const createSessionWithFirstMessage = async (firstMessage: string) => {
    const session = await createSessionMutation.mutateAsync({
      session_metadata: {
        firstMessage: firstMessage,
      },
    });
    return session;
  };

  const updateSessionWithFirstMessage = async (
    sessionId: string,
    firstMessage: string,
  ) => {
    const session = sessionsQuery.data?.find((s) => s.id === sessionId);
    if (!session) return;

    const updatedMetadata = {
      ...session.session_metadata,
      firstMessage: firstMessage,
    };

    return updateSessionMutation.mutateAsync({
      sessionId,
      data: { session_metadata: updatedMetadata },
    });
  };

  return {
    // Data
    sessions: sortedSessions,
    pinnedSessions,
    regularSessions,
    rawSessions: sessionsQuery.data || [],

    // Status
    isLoading: sessionsQuery.isLoading,
    isError: sessionsQuery.isError,
    isCreating: createSessionMutation.isPending,

    // Actions
    createSession: createSessionMutation.mutateAsync,
    updateSession: updateSessionMutation.mutateAsync,
    createSessionWithFirstMessage,
    updateSessionWithFirstMessage,

    // New actions for session management
    renameSession: renameSessionMutation.mutateAsync,
    togglePinSession: togglePinSessionMutation.mutateAsync,
    deleteSession: deleteSessionMutation.mutateAsync,

    // Loading states for new actions
    isRenamingSession: renameSessionMutation.isPending,
    isTogglingPin: togglePinSessionMutation.isPending,
    isDeletingSession: deleteSessionMutation.isPending,
  };
};
