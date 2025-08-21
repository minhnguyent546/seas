import {
  ChatsService,
  type ChatSessionCreate,
  type ChatSessionPublic,
  type ChatSessionUpdate,
  type ChatsGetChatSessionsData,
} from '@/client';
import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
  type InfiniteData,
} from '@tanstack/react-query';
import { useMemo } from 'react';

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

  return 'New Chat';
};

export interface ChatSessionItem {
  id: string;
  label: string;
  isPinned?: boolean;
}

export const useChatSessions = () => {
  const queryClient = useQueryClient();

  const PAGE_SIZE = 30;

  const sessionsQuery = useInfiniteQuery({
    queryKey: CHAT_QUERY_KEYS.sessions,
    initialPageParam: 0 as number, // offset
    queryFn: async ({ pageParam }) => {
      try {
        const getChatSessionsData: ChatsGetChatSessionsData = {
          offset: pageParam as number,
          limit: PAGE_SIZE,
          sortBy: 'created_at',
          sortOrder: 'desc',
        };
        const sessions =
          await ChatsService.getChatSessions(getChatSessionsData);

        // If user has no sessions, automatically create one
        if ((pageParam as number) === 0 && sessions.length === 0) {
          const newSession = await ChatsService.createChatSession({
            requestBody: { session_metadata: {} },
          });
          // Return the new session as the only page item
          return [newSession];
        }

        return sessions;
      } catch (error) {
        console.error('Failed to fetch chat sessions:', error);
        throw error;
      }
    },
    getNextPageParam: (lastPage, allPages) => {
      // If the last page returned fewer than PAGE_SIZE, there are no more pages
      if (!lastPage || lastPage.length < PAGE_SIZE) return undefined;
      // Compute next offset by number of pages loaded to avoid brittleness from optimistic updates
      const nextOffset = allPages.length * PAGE_SIZE;
      return nextOffset;
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
      data: ChatSessionUpdate;
    }) => {
      return ChatsService.updateChatSession({
        chatSessionId: sessionId,
        requestBody: data,
      });
    },
    onMutate: async ({ sessionId, data }) => {
      await queryClient.cancelQueries({ queryKey: CHAT_QUERY_KEYS.sessions });

      // Also cancel any in-flight fetch for this session
      await queryClient.cancelQueries({
        queryKey: CHAT_QUERY_KEYS.session(sessionId),
      });

      const previousSessions = queryClient.getQueryData<
        InfiniteData<ChatSessionPublic[], number>
      >(CHAT_QUERY_KEYS.sessions);
      const previousSession = queryClient.getQueryData<ChatSessionPublic>(
        CHAT_QUERY_KEYS.session(sessionId),
      );

      const applyUpdate = (
        session: ChatSessionPublic,
        update: Record<string, unknown>,
      ): ChatSessionPublic => {
        let updated: ChatSessionPublic = { ...session } as ChatSessionPublic;
        if (update && typeof update === 'object') {
          for (const key of Object.keys(update)) {
            if (
              key === 'session_metadata' &&
              typeof (update as any).session_metadata === 'object'
            ) {
              updated = {
                ...updated,
                session_metadata: {
                  ...updated.session_metadata,
                  ...(update as any).session_metadata,
                },
              } as ChatSessionPublic;
            } else {
              (updated as any)[key] = (update as any)[key];
            }
          }
        }
        return updated;
      };

      // Optimistically update sessions list across pages
      queryClient.setQueryData<
        InfiniteData<ChatSessionPublic[], number> | undefined
      >(CHAT_QUERY_KEYS.sessions, (old) => {
        if (!old) return old;
        return {
          pageParams: old.pageParams,
          pages: old.pages.map((page) =>
            page.map((chat) =>
              chat.id === sessionId ? applyUpdate(chat, data || {}) : chat,
            ),
          ),
        };
      });

      // Optimistically update individual session cache if present
      queryClient.setQueryData<ChatSessionPublic | undefined>(
        CHAT_QUERY_KEYS.session(sessionId),
        (old) => (old ? applyUpdate(old, data || {}) : old),
      );

      return { previousSessions, previousSession };
    },
    onError: (_err, variables, context) => {
      if (context?.previousSessions) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.sessions,
          context.previousSessions,
        );
      }
      if (context?.previousSession && variables?.sessionId) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.session(variables.sessionId),
          context.previousSession,
        );
      }
    },
    onSuccess: (updatedSession) => {
      if (!updatedSession) return;
      queryClient.setQueryData<
        InfiniteData<ChatSessionPublic[], number> | undefined
      >(CHAT_QUERY_KEYS.sessions, (old) => {
        if (!old) return old;
        return {
          pageParams: old.pageParams,
          pages: old.pages.map((page) =>
            page.map((chat) =>
              chat.id === updatedSession.id ? updatedSession : chat,
            ),
          ),
        };
      });
      queryClient.setQueryData<ChatSessionPublic | undefined>(
        CHAT_QUERY_KEYS.session(updatedSession.id),
        updatedSession,
      );
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
      const session = sessionsQuery.data?.pages
        .flat()
        .find((s) => s.id === sessionId);
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

    // Optimistic update
    onMutate: async ({ sessionId, newTitle }) => {
      await queryClient.cancelQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
      await queryClient.cancelQueries({
        queryKey: CHAT_QUERY_KEYS.session(sessionId),
      });

      // Snapshot current state
      const previousSessions = queryClient.getQueryData<
        InfiniteData<ChatSessionPublic[], number>
      >(CHAT_QUERY_KEYS.sessions);

      const previousSession = queryClient.getQueryData<ChatSessionPublic>(
        CHAT_QUERY_KEYS.session(sessionId),
      );

      // Optimistically update sessions list across pages
      queryClient.setQueryData<
        InfiniteData<ChatSessionPublic[], number> | undefined
      >(CHAT_QUERY_KEYS.sessions, (old) => {
        if (!old) return old;
        return {
          pageParams: old.pageParams,
          pages: old.pages.map((page) =>
            page.map((chat) =>
              chat.id === sessionId
                ? {
                    ...chat,
                    session_metadata: {
                      ...chat.session_metadata,
                      firstMessage: newTitle,
                    },
                  }
                : chat,
            ),
          ),
        };
      });

      // Optimistically update individual session cache if present
      queryClient.setQueryData<ChatSessionPublic | undefined>(
        CHAT_QUERY_KEYS.session(sessionId),
        (old) =>
          old
            ? {
                ...old,
                session_metadata: {
                  ...old.session_metadata,
                  firstMessage: newTitle,
                },
              }
            : old,
      );

      return { previousSessions, previousSession };
    },

    // Rollback on error
    onError: (_err, variables, context) => {
      if (context?.previousSessions) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.sessions,
          context.previousSessions,
        );
      }
      if (context?.previousSession && variables?.sessionId) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.session(variables.sessionId),
          context.previousSession,
        );
      }
    },

    // Refetch for consistency
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
      if (variables?.sessionId) {
        queryClient.invalidateQueries({
          queryKey: CHAT_QUERY_KEYS.session(variables.sessionId),
        });
      }
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
    onMutate: async ({ sessionId, isPinned }) => {
      await queryClient.cancelQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
      await queryClient.cancelQueries({
        queryKey: CHAT_QUERY_KEYS.session(sessionId),
      });

      const previousSessions = queryClient.getQueryData<
        InfiniteData<ChatSessionPublic[], number>
      >(CHAT_QUERY_KEYS.sessions);
      const previousSession = queryClient.getQueryData<ChatSessionPublic>(
        CHAT_QUERY_KEYS.session(sessionId),
      );

      // Optimistically update sessions list across pages
      queryClient.setQueryData<
        InfiniteData<ChatSessionPublic[], number> | undefined
      >(CHAT_QUERY_KEYS.sessions, (old) => {
        if (!old) return old;
        return {
          pageParams: old.pageParams,
          pages: old.pages.map((page) =>
            page.map((chat) =>
              chat.id === sessionId ? { ...chat, is_favorite: isPinned } : chat,
            ),
          ),
        };
      });

      // Optimistically update individual session cache if present
      queryClient.setQueryData<ChatSessionPublic | undefined>(
        CHAT_QUERY_KEYS.session(sessionId),
        (old) => (old ? { ...old, is_favorite: isPinned } : old),
      );

      return { previousSessions, previousSession };
    },
    onError: (_err, variables, context) => {
      if (context?.previousSessions) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.sessions,
          context.previousSessions,
        );
      }
      if (context?.previousSession && variables?.sessionId) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.session(variables.sessionId),
          context.previousSession,
        );
      }
    },
    onSuccess: (updatedSession) => {
      if (!updatedSession) return;
      queryClient.setQueryData<
        InfiniteData<ChatSessionPublic[], number> | undefined
      >(CHAT_QUERY_KEYS.sessions, (old) => {
        if (!old) return old;
        return {
          pageParams: old.pageParams,
          pages: old.pages.map((page) =>
            page.map((chat) =>
              chat.id === updatedSession.id ? updatedSession : chat,
            ),
          ),
        };
      });
      queryClient.setQueryData<ChatSessionPublic | undefined>(
        CHAT_QUERY_KEYS.session(updatedSession.id),
        updatedSession,
      );
    },
  });

  // Mutation for delete session
  const deleteSessionMutation = useMutation({
    mutationFn: async ({ sessionId }: { sessionId: string }) => {
      return ChatsService.deleteChatSession({
        chatSessionId: sessionId,
      });
    },
    onMutate: async ({ sessionId }: { sessionId: string }) => {
      await queryClient.cancelQueries({ queryKey: CHAT_QUERY_KEYS.sessions });
      await queryClient.cancelQueries({
        queryKey: CHAT_QUERY_KEYS.session(sessionId),
      });

      const previousSessions = queryClient.getQueryData<
        InfiniteData<ChatSessionPublic[], number>
      >(CHAT_QUERY_KEYS.sessions);
      const previousSession = queryClient.getQueryData<ChatSessionPublic>(
        CHAT_QUERY_KEYS.session(sessionId),
      );

      // Optimistically remove from sessions list across pages
      queryClient.setQueryData<
        InfiniteData<ChatSessionPublic[], number> | undefined
      >(CHAT_QUERY_KEYS.sessions, (old) => {
        if (!old) return old;
        return {
          pageParams: old.pageParams,
          pages: old.pages.map((page) =>
            page.filter((chat) => chat.id !== sessionId),
          ),
        };
      });

      // Remove individual session cache for the deleted id
      queryClient.removeQueries({
        queryKey: CHAT_QUERY_KEYS.session(sessionId),
      });

      return { previousSessions, previousSession };
    },
    onError: (_err, variables, context) => {
      if (context?.previousSessions) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.sessions,
          context.previousSessions,
        );
      }
      if (context?.previousSession && variables?.sessionId) {
        queryClient.setQueryData(
          CHAT_QUERY_KEYS.session(variables.sessionId),
          context.previousSession,
        );
      }
    },
    // No invalidation to avoid extra latency; backend is source of truth but cache already reflects deletion
  });

  const sessionsData: ChatSessionPublic[] =
    sessionsQuery.data?.pages.flat() || [];

  // Transform sessions to the format expected by the Sidebar
  const transformedSessions: ChatSessionItem[] = useMemo(
    () =>
      sessionsData.map((session) => ({
        id: session.id,
        label: getSessionTitle(session),
        isPinned: session.is_favorite,
      })),
    [sessionsData],
  );

  // Backend returns sessions sorted by created_at desc; preserve order and only split into groups
  const pinnedSessions = useMemo(
    () => transformedSessions.filter((s) => s.isPinned),
    [transformedSessions],
  );
  const regularSessions = useMemo(
    () => transformedSessions.filter((s) => !s.isPinned),
    [transformedSessions],
  );

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
    const session = sessionsQuery.data?.pages
      .flat()
      .find((s) => s.id === sessionId);
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
    sessions: transformedSessions,
    pinnedSessions,
    regularSessions,
    rawSessions: sessionsData,

    // Status
    isLoading: sessionsQuery.isLoading,
    isError: sessionsQuery.isError,
    isCreating: createSessionMutation.isPending,
    hasNextPage: sessionsQuery.hasNextPage,
    isFetchingNextPage: sessionsQuery.isFetchingNextPage,

    // Actions
    createSession: createSessionMutation.mutateAsync,
    updateSession: updateSessionMutation.mutateAsync,
    createSessionWithFirstMessage,
    updateSessionWithFirstMessage,
    fetchNextPage: sessionsQuery.fetchNextPage,

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
