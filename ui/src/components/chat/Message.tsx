import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { formatDate } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';

interface MessageProps {
  message: MessageType;
  isLastMessage?: boolean;
}

export const UserMessage: React.FC<MessageProps> = ({ message }) => {
  return (
    <div className="group flex justify-end py-4">
      <div className="max-w-[80%] space-y-2">
        <div className="flex items-center justify-end gap-2">
          <div className="text-xs text-gray-500">
            {formatDate(message.timestamp)}
          </div>
        </div>
        <div className="prose prose-sm dark:prose-invert bg-gray-50 dark:bg-gray-800 p-3 rounded-xl">
          {message.content}
        </div>
      </div>
    </div>
  );
};

export const BotMessage: React.FC<MessageProps> = ({ message }) => {
  return (
    <div className="group relative flex items-start gap-4 py-4">
      <Avatar className="rounded-xl">
        <AvatarFallback className="bg-primary text-white rounded-xl">
          AI
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <div className="text-xs text-gray-500">
            {formatDate(message.timestamp)}
          </div>
        </div>
        <div className="prose prose-sm max-w-none dark:prose-invert p-4 rounded-xl">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
          >
            {message.content}
          </ReactMarkdown>
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

export const Message: React.FC<MessageProps> = ({ message }) => {
  switch (message.role) {
    case 'user':
      return <UserMessage message={message} />;
    case 'assistant':
      return <BotMessage message={message} />;
    case 'system':
      return <SystemMessage message={message} />;
    default:
      return null;
  }
};
