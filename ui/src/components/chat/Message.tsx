import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import {
  IconCopy,
  IconSparkles,
  IconThumbDown,
  IconThumbUp,
} from '@tabler/icons-react';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.min.css';
import MarkdownIt from 'markdown-it';
import React, { useEffect, useMemo, useRef, useState } from 'react';

interface MessageProps {
  message: MessageType;
  isLastMessage?: boolean;
  isLoading?: boolean;
}

const md: MarkdownIt = new MarkdownIt({
  html: true, // Enable HTML tags in source
  xhtmlOut: false, // Use HTML5 output
  breaks: true, // Convert '\n' in paragraphs into <br>
  linkify: true, // Auto-convert URL-like text to links
  typographer: true, // Enable quotes beautification and other typography
  highlight: function (str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
      } catch (__) {}
    }
    return md.utils.escapeHtml(str);
  },
});

// Custom hook for rendering markdown with markdown-it (simplified)
const useMarkdownRenderer = (content: string) => {
  return useMemo(() => {
    const rendered = md.render(content);
    const sanitized = DOMPurify.sanitize(rendered);
    return sanitized;
  }, [content]);
};

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
  isLastMessage = false,
}) => {
  const [displayText, setDisplayText] = useState('');
  const timeoutRef = useRef<number | undefined>(undefined);

  const isEmptyAndLoading = !message.content && isLoading;
  const renderedMarkdown = useMarkdownRenderer(displayText);

  // Typing effect
  useEffect(() => {
    if (!message.content) {
      setDisplayText('');
      return;
    }

    // Only apply typing effect to the last message
    if (isLastMessage && message.content.length > displayText.length) {
      const typeText = () => {
        setDisplayText((prev) => {
          if (prev.length < message.content.length) {
            // Type multiple characters at once for faster effect
            const charsToAdd = Math.min(
              10,
              message.content.length - prev.length,
            );
            return message.content.slice(0, prev.length + charsToAdd);
          } else {
            return prev;
          }
        });
      };

      // Clear existing timeout
      if (timeoutRef.current !== undefined) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = window.setTimeout(typeText, 5);
    } else {
      // For non-last messages or when content is shorter, show immediately
      setDisplayText(message.content);
    }

    return () => {
      if (timeoutRef.current !== undefined) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [message.content, isLastMessage, displayText.length]);

  return (
    <div className="group relative flex items-start pb-4">
      <div className="flex-1 space-y-2">
        <div className="p-4 pl-0 pb-0 rounded-xl bg-white dark:bg-gray-900">
          {isEmptyAndLoading ? (
            <div className="flex items-center py-4">
              <IconSparkles className="h-3 w-3 text-primary animate-ping" />
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
        />
      );
    case 'system':
      return <SystemMessage message={message} />;
    default:
      return null;
  }
};
