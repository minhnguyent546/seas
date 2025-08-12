import { SeasLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { useMarkdownRenderer } from '@/hooks/useMarkdownRenderer';
import { useMessageActions } from '@/hooks/useMessageActions';
import { useTypingEffect } from '@/hooks/useTypingEffect';
import { formatDate } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import { IconCopy, IconThumbDown, IconThumbUp } from '@tabler/icons-react';
import React from 'react';

interface MessageProps {
  message: MessageType;
  isLastMessage?: boolean;
  isLoading?: boolean;
  isLoadingFromBackend?: boolean;
}

export const UserMessage: React.FC<MessageProps> = ({ message }) => {
  return (
    <div className="group flex justify-end py-4">
      <div className="max-w-[80%] space-y-2">
        <div className="prose prose-sm dark:prose-invert bg-gray-50 dark:bg-gray-800 p-3 rounded-xl">
          {message.content}
        </div>
        <div className="flex items-center justify-end gap-2">
          <div className="text-xs text-gray-500">
            {formatDate(message.timestamp)}
          </div>
        </div>
      </div>
    </div>
  );
};

export const BotMessage: React.FC<MessageProps> = ({
  message,
  isLoading = false,
  isLastMessage = false,
  isLoadingFromBackend = false,
}) => {
  // Only apply typing effect if this is the last message, not loading from backend, and has content
  const shouldUseTypingEffect =
    isLastMessage && !isLoadingFromBackend && Boolean(message.content);
  const displayText = useTypingEffect(message.content, shouldUseTypingEffect);
  const renderedMarkdown = useMarkdownRenderer(displayText);
  const { handleCopyMessage, handleLikeMessage, handleDislikeMessage } =
    useMessageActions();

  const isEmptyAndLoading = !message.content && isLoading;

  return (
    <div className="group relative flex items-start pb-4">
      <div className="flex-1 space-y-2">
        <div className="p-4 pl-0 pb-0 rounded-xl bg-white dark:bg-gray-900">
          {isEmptyAndLoading ? (
            <div className="flex items-center py-4">
              <SeasLogo size={12} className="animate-ping text-primary" />
            </div>
          ) : (
            <div
              className="prose prose-sm max-w-none dark:prose-invert break-words"
              dangerouslySetInnerHTML={{ __html: renderedMarkdown }}
            />
          )}
        </div>
        {!isEmptyAndLoading && (
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500">
              {formatDate(message.timestamp)}
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 animate-in fade-in-0 slide-in-from-left-2 duration-300"
                onClick={() => handleCopyMessage(message.content)}
                title="Copy"
              >
                <IconCopy className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 animate-in fade-in-0 slide-in-from-left-2 duration-300"
                onClick={() => handleLikeMessage(message.id)}
                title="Useful"
              >
                <IconThumbUp className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 animate-in fade-in-0 slide-in-from-left-2 duration-300"
                onClick={() => handleDislikeMessage(message.id)}
                title="Needs improvement"
              >
                <IconThumbDown className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const SystemMessage: React.FC<MessageProps> = ({ message }) => {
  return (
    <div className="flex justify-center py-4">
      <div className="rounded-xl bg-gray-100 px-4 py-2 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300 shadow-sm">
        {message.content}
      </div>
    </div>
  );
};

export const Message: React.FC<MessageProps> = ({
  message,
  isLoading,
  isLastMessage,
  isLoadingFromBackend,
}) => {
  switch (message.role) {
    case 'user':
      return <UserMessage message={message} />;
    case 'assistant':
      return (
        <BotMessage
          message={message}
          isLoading={isLoading}
          isLastMessage={isLastMessage}
          isLoadingFromBackend={isLoadingFromBackend}
        />
      );
    case 'system':
      return <SystemMessage message={message} />;
    default:
      return null;
  }
};
