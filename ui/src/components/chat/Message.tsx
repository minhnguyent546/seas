import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/utils';
import '@/styles/prism-theme.css';
import type { Message as MessageType } from '@/types/chat';
import {
  IconCopy,
  IconSparkles,
  IconThumbDown,
  IconThumbUp,
} from '@tabler/icons-react';
import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';

interface MessageProps {
  message: MessageType;
  isLastMessage?: boolean;
  isLoading?: boolean;
}

// Message action handlers
const handleCopyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content);
    // TODO: add toast notification here
  } catch (error) {
    console.error('Failed to copy message:', error);
  }
};

const handleLikeMessage = (messageId: string) => {
  // TODO: implement like functionality
  console.log('Liked message:', messageId);
};

const handleDislikeMessage = (messageId: string) => {
  // TODO: implement dislike functionality
  console.log('Disliked message:', messageId);
};

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
}) => {
  const isEmptyAndLoading = !message.content && isLoading;

  return (
    <div className="group relative flex items-start pb-4">
      <div className="flex-1 space-y-2">
        <div className="p-4 pl-0 pb-0 rounded-xl bg-white dark:bg-gray-900">
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {isEmptyAndLoading ? (
              <div className="flex items-center py-4">
                <IconSparkles className="h-3 w-3 text-primary animate-ping" />
              </div>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw, rehypeSanitize]}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-xs text-gray-500">
            {formatDate(message.timestamp)}
          </div>
          {!isEmptyAndLoading && (
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
          )}
        </div>
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

export const Message: React.FC<MessageProps> = ({ message, isLoading }) => {
  switch (message.role) {
    case 'user':
      return <UserMessage message={message} />;
    case 'assistant':
      return <BotMessage message={message} isLoading={isLoading} />;
    case 'system':
      return <SystemMessage message={message} />;
    default:
      return null;
  }
};
