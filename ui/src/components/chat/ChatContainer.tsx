import { ChatInput } from '@/components/chat/ChatInput';
import { Message } from '@/components/chat/Message';
import { RecommendedQuestions } from '@/components/chat/RecommendedQuestions';
import { useAutoScroll } from '@/hooks/useAutoScroll';
import { useChat } from '@/hooks/useChat';
import { IconSparkles } from '@tabler/icons-react';
import React, { useEffect } from 'react';

interface ChatContainerProps {
  userName: string;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({ userName }) => {
  const { messages, isLoading, handleSendMessage, cleanup } = useChat();
  const { scrollRef } = useAutoScroll(messages);

  // Cleanup function to abort ongoing requests
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

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
            <div className="space-y-4 pb-8">
              {messages.map((message, index) => (
                <Message
                  key={message.id}
                  message={message}
                  isLastMessage={index === messages.length - 1}
                  isLoading={isLoading && index === messages.length - 1}
                />
              ))}
              <div
                ref={scrollRef}
                className="h-0 w-0 overflow-hidden"
                aria-hidden="true"
                role="presentation"
              />
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
