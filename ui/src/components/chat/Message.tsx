import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import type { Message as MessageType } from '@/types/chat';
import { formatDate } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface MessageProps {
  message: MessageType;
  isLastMessage?: boolean;
}

export const UserMessage: React.FC<MessageProps> = ({ message }) => {
  return (
    <div className="group flex items-start gap-4 py-4">
      <Avatar className="rounded-xl">
        <AvatarImage src="/user-avatar.png" alt="User" />
        <AvatarFallback className="bg-blue-600 text-white rounded-xl">
          U
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <div className="font-medium">You</div>
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
          <div className="font-medium">AI Assistant</div>
          <div className="text-xs text-gray-500">
            {formatDate(message.timestamp)}
          </div>
        </div>
        <div className="prose prose-sm max-w-none dark:prose-invert bg-primary/5 dark:bg-primary/10 p-4 rounded-xl">
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
