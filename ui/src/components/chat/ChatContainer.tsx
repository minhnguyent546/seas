import { OpenAPI } from '@/client';
import { ChatInput } from '@/components/chat/ChatInput';
import { Message } from '@/components/chat/Message';
import { RecommendedQuestions } from '@/components/chat/RecommendedQuestions';
import { generateId } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import { IconSparkles } from '@tabler/icons-react';
import React, { useEffect, useRef, useState } from 'react';

interface ChatContainerProps {
  userName: string;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({ userName }) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Cleanup function to abort ongoing requests
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const streamResponse = async (userMessage: string) => {
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
  };

  const handleSendMessage = async (content: string) => {
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
  };

  const handleQuestionClick = (question: string) => {
    handleSendMessage(question);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        <div className="mx-auto w-full max-w-[var(--content-max-width)] h-full">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <IconSparkles className="h-10 w-10 text-primary" />
              </div>
              <h1 className="mb-2 text-3xl font-bold tracking-tight text-gray-800 dark:text-white sm:text-4xl">
                Hi, {userName}!
              </h1>
              <p className="mb-8 text-lg text-gray-500 dark:text-gray-400">
                Ask me anything about CTU Enrollment Program
              </p>
              <div className="w-full max-w-2xl">
                <RecommendedQuestions onQuestionClick={handleQuestionClick} />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <Message
                  key={message.id}
                  message={message}
                  isLastMessage={
                    message.id === messages[messages.length - 1].id
                  }
                  isLoading={
                    isLoading && message.id === messages[messages.length - 1].id
                  }
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      <div className="pb-4 rounded-b-xl flex-shrink-0">
        <div className="mx-auto w-full max-w-[var(--content-max-width)]">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
};
