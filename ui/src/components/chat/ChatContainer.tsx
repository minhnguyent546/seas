import { ChatInput } from '@/components/chat/ChatInput';
import { Message } from '@/components/chat/Message';
import { RecommendedQuestions } from '@/components/chat/RecommendedQuestions';
import { generateId } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import { Box, CircularProgress } from '@mui/material';
import { IconSparkles } from '@tabler/icons-react';
import React, { useEffect, useRef, useState } from 'react';

interface ChatContainerProps {
  userName: string;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({ userName }) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Mock function to simulate AI response
  const simulateResponse = async (userMessage: string) => {
    setIsLoading(true);

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const botResponse: MessageType = {
      id: generateId(),
      role: 'assistant',
      content: `Hello ${userName}, I received your message: "${userMessage}". How can I help you further?`,
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, botResponse]);
    setIsLoading(false);
  };

  const handleSendMessage = async (content: string) => {
    const userMessage: MessageType = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    await simulateResponse(content);
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
                />
              ))}
              {isLoading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                  <CircularProgress size={30} />
                </Box>
              )}
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
