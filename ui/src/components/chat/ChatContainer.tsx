import { ChatInput } from '@/components/chat/ChatInput';
import { Message } from '@/components/chat/Message';
import { RecommendedQuestions } from '@/components/chat/RecommendedQuestions';
import { SeasLogo } from '@/components/icons';
import { useAutoScroll } from '@/hooks/useAutoScroll';
import { useChat } from '@/hooks/useChat';
import { useLanguage } from '@/hooks/useLanguage';
import React, { useCallback, useRef } from 'react';

interface ChatContainerProps {
  userName: string;
  sessionId?: string;
  onFirstMessage?: (message: string) => Promise<void>;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  userName,
  sessionId,
  onFirstMessage,
}) => {
  const { messages, isLoading, isLoadingMessages, handleSendMessage } = useChat(
    { sessionId },
  );
  const { scrollRef } = useAutoScroll(messages);
  const { t } = useLanguage();
  const hasHandledFirstMessage = useRef(false);

  const handleMessageSend = useCallback(
    async (message: string) => {
      // Handle first message update for existing sessions (non-blocking)
      if (
        sessionId &&
        !hasHandledFirstMessage.current &&
        messages.length === 0 &&
        onFirstMessage
      ) {
        hasHandledFirstMessage.current = true;
        // Let it run in background to avoid blocking UI
        onFirstMessage(message).catch((error) => {
          console.error('Failed to handle first message:', error);
        });
      }

      // Send the message normally
      await handleSendMessage(message);
    },
    [sessionId, messages.length, onFirstMessage, handleSendMessage],
  );

  React.useEffect(() => {
    hasHandledFirstMessage.current = false;
  }, [sessionId]);

  const handleQuestionClick = (question: string) => {
    handleMessageSend(question);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        <div className="mx-auto w-full max-w-[var(--content-max-width)] h-full">
          {isLoadingMessages ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-primary"></div>
              </div>
              <p className="text-lg text-gray-500 dark:text-gray-400">
                {t('chat.loadingConversation')}
              </p>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full">
                <SeasLogo size={80} className="text-primary" />
              </div>
              <h1 className="mb-2 text-3xl font-bold tracking-tight text-gray-800 dark:text-white sm:text-4xl">
                {t('chat.welcomeGreeting', { name: userName })}
              </h1>
              <p className="mb-8 text-lg text-gray-500 dark:text-gray-400">
                {t('chat.welcomeMessage')}
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
        <div className="mx-auto w-full max-w-[var(--content-max-width)] px-4">
          <ChatInput onSendMessage={handleMessageSend} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
};
