import React, { useState, useRef, useEffect } from 'react';
import { ChatInput } from '@/components/chat/ChatInput';
import { Message } from '@/components/chat/Message';
import { ChatFeatures } from '@/components/chat/ChatFeatures';
import { generateId } from '@/lib/utils';
import type { Message as MessageType, ChatFeature } from '@/types/chat';

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

  const handleFeatureClick = (feature: ChatFeature) => {
    // Handle feature selection
    const systemMessage: MessageType = {
      id: generateId(),
      role: 'system',
      content: `You selected the ${feature.title} feature`,
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, systemMessage]);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        <div className="mx-auto w-full max-w-[var(--content-max-width)]">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center">
              <h1 className="mb-2 text-3xl font-semibold text-gray-800 dark:text-white">
                Hi, {userName}!
              </h1>
              <p className="mb-8 text-lg text-gray-600 dark:text-gray-300">
                How can I assist you today?
              </p>
              <div className="w-full">
                <ChatFeatures onFeatureClick={handleFeatureClick} />
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
