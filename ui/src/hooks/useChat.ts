import { OpenAPI } from '@/client';
import { generateId } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import { useCallback, useRef, useState } from 'react';

export const useChat = () => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const streamResponse = useCallback(async (userMessage: string) => {
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

    try {
      const response = await fetch(`${OpenAPI.BASE}/api/v1/chatbot/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/stream',
        },
        body: JSON.stringify({
          query: userMessage,
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

      // Final update is already handled in the streaming loop above
    } catch (error) {
      console.error('Streaming error:', error);

      // Update the bot message with error content
      const errorMessage =
        error instanceof Error ? error.message : 'An error occurred';
      setMessages((prevMessages) =>
        prevMessages.map((msg) =>
          msg.id === botResponse.id
            ? { ...msg, content: `Error: ${errorMessage}` }
            : msg,
        ),
      );
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  const handleSendMessage = useCallback(
    async (content: string) => {
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

      setMessages((prevMessages) => [...prevMessages, userMessage]);
      await streamResponse(content);
    },
    [streamResponse],
  );

  // Cleanup function to abort ongoing requests
  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    messages,
    isLoading,
    handleSendMessage,
    cleanup,
  };
};
