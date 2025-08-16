import { ChatsService, OpenAPI } from '@/client';
import { generateId, getErrorMessage } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import { useCallback, useEffect, useRef, useState } from 'react';

interface UseChatProps {
  sessionId?: string;
}

export const useChat = ({ sessionId }: UseChatProps = {}) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isLoadingFromBackend, setIsLoadingFromBackend] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cleanup function to abort ongoing requests
  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  // Auto-cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  // Load messages from backend when sessionId changes
  useEffect(() => {
    if (sessionId) {
      loadMessages(sessionId);
    } else {
      // Clear messages if no session
      setMessages([]);
    }
  }, [sessionId]);

  // Function to load messages from backend
  const loadMessages = async (chatSessionId: string) => {
    if (!chatSessionId) return;

    setIsLoadingMessages(true);
    setIsLoadingFromBackend(true);
    try {
      const response = await ChatsService.getChatMessages({ chatSessionId });

      // Convert backend messages to our message format
      const backendMessages = Array.isArray(response) ? response : [];
      const convertedMessages: MessageType[] = backendMessages.map(
        (msg: any) => ({
          id: msg.id || generateId(),
          role:
            msg.sender === 'USER'
              ? 'user'
              : msg.sender === 'BOT'
                ? 'assistant'
                : 'system',
          content: msg.content || '',
          // Parse ISO datetime format like "2025-08-11T16:34:53.066705Z"
          timestamp: new Date(msg.created_at || new Date()),
        }),
      );

      setMessages(convertedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      // Don't clear messages on error, keep current state
    } finally {
      setIsLoadingMessages(false);
      // Clear the flag after a short delay to ensure typing effect doesn't trigger
      setTimeout(() => {
        setIsLoadingFromBackend(false);
      }, 100);
    }
  };

  const streamResponse = useCallback(
    async (userMessage: string, chatSessionId?: string) => {
      setIsLoading(true);

      // Create abort controller for this request
      abortControllerRef.current = new AbortController();

      const botResponse: MessageType = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };

      // Add the initial empty bot message
      setMessages((prevMessages) => [...prevMessages, botResponse]);

      let response: Response | undefined;

      try {
        response = await fetch(`${OpenAPI.BASE}/api/v1/chatbot/query`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/plain',
          },
          body: JSON.stringify({
            query: userMessage,
            chat_session_id: chatSessionId ?? null,
          }),
          signal: abortControllerRef.current.signal,
          credentials: OpenAPI.CREDENTIALS,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No reader available');
        }

        let accumulatedContent = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // Decode the chunk
          const chunk = decoder.decode(value, { stream: true });

          accumulatedContent += chunk;

          // Update the message with the processed content
          setMessages((prevMessages) =>
            prevMessages.map((msg) =>
              msg.id === botResponse.id
                ? { ...msg, content: accumulatedContent }
                : msg,
            ),
          );
        }

        // Set final timestamp when response completes
        setMessages((prevMessages) =>
          prevMessages.map((msg) =>
            msg.id === botResponse.id ? { ...msg, timestamp: new Date() } : msg,
          ),
        );
      } catch (error) {
        console.error('Streaming error:', error);

        // Get user-friendly error message
        const errorMessage = await getErrorMessage(error, response);

        const finalErrorContent = `❌ **Error**: ${errorMessage}${error instanceof Error && error.name === 'AbortError' ? '' : '\n\nPlease try again.'}`;

        setMessages((prevMessages) =>
          prevMessages.map((msg) =>
            msg.id === botResponse.id
              ? { ...msg, content: finalErrorContent, timestamp: new Date() }
              : msg,
          ),
        );
      } finally {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    },
    [],
  );

  const handleSendMessage = useCallback(
    async (content: string) => {
      // Ensure session is available before sending message
      if (!sessionId) {
        console.warn('Cannot send message: no active session');
        return;
      }

      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const userMessage: MessageType = {
        id: generateId(),
        role: 'user',
        content,
        timestamp: new Date(),
      };

      // Add user message to UI immediately (optimistic update)
      setMessages((prevMessages) => [...prevMessages, userMessage]);

      // Stream the response; backend persists user and bot messages for the session
      await streamResponse(content, sessionId);
    },
    [streamResponse, sessionId],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    isLoadingMessages,
    isLoadingFromBackend,
    handleSendMessage,
    clearMessages,
    loadMessages,
  };
};
