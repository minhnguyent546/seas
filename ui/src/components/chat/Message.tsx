import { type ChatMessageFeedbackType } from '@/client';
import { MessageFeedbackForm } from '@/components/chat/MessageFeedbackForm';
import { SeasLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { useMarkdownRenderer } from '@/hooks/useMarkdownRenderer';
import { useMessageActions } from '@/hooks/useMessageActions';
import { useTypingEffect } from '@/hooks/useTypingEffect';
import { formatMessageDate } from '@/lib/utils';
import type { Message as MessageType } from '@/types/chat';
import { IconCopy, IconThumbDown, IconThumbUp } from '@tabler/icons-react';
import React, { useCallback, useState } from 'react';

interface MessageProps {
  message: MessageType;
  isLastMessage?: boolean;
  isLoading?: boolean;
  isLoadingFromBackend?: boolean;
  onSubmitFeedback?: (args: {
    messageId: string;
    feedback: ChatMessageFeedbackType;
    detail?: string;
  }) => Promise<void>;
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
            {formatMessageDate(message.timestamp)}
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
  onSubmitFeedback,
}) => {
  // Only apply typing effect if this is the last message, not loading from backend, and has content
  const shouldUseTypingEffect =
    isLastMessage && !isLoadingFromBackend && Boolean(message.content);
  const displayText = useTypingEffect(message.content, shouldUseTypingEffect);
  const renderedMarkdown = useMarkdownRenderer(displayText);
  const { handleCopyMessage } = useMessageActions();

  const isEmptyAndLoading = !message.content && isLoading;
  const [feedbackIntent, setFeedbackIntent] = useState<
    null | 'like' | 'dislike'
  >(null);

  const hasFeedback = Boolean(message.feedback);
  const isLike = hasFeedback && String(message.feedback).startsWith('LIKE');

  const handleSubmitFeedback = useCallback(
    async (payload: { feedback: ChatMessageFeedbackType; detail?: string }) => {
      if (!onSubmitFeedback) return;
      await onSubmitFeedback({
        messageId: message.backendId || message.id,
        feedback: payload.feedback,
        detail: payload.detail,
      });
      setFeedbackIntent(null);
    },
    [message.backendId, message.id, onSubmitFeedback],
  );

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
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <div className="text-xs text-gray-500">
                {formatMessageDate(message.timestamp)}
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 animate-in fade-in-0 slide-in-from-left-2 duration-300 cursor-pointer"
                  onClick={() => handleCopyMessage(message.content)}
                  title="Copy"
                >
                  <IconCopy className="h-4 w-4" />
                </Button>
                {hasFeedback ? (
                  isLike ? (
                    <Button
                      variant="outline"
                      size="icon"
                      disabled
                      className="h-8 w-8 bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700"
                      title="Feedback: Like"
                    >
                      <IconThumbUp className="h-4 w-4" />
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="icon"
                      disabled
                      className="h-8 w-8 bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700"
                      title="Feedback: Dislike"
                    >
                      <IconThumbDown className="h-4 w-4" />
                    </Button>
                  )
                ) : (
                  <>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 animate-in fade-in-0 slide-in-from-left-2 duration-300 cursor-pointer"
                      onClick={() => setFeedbackIntent('like')}
                      title="Useful"
                    >
                      <IconThumbUp className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 animate-in fade-in-0 slide-in-from-left-2 duration-300 cursor-pointer"
                      onClick={() => setFeedbackIntent('dislike')}
                      title="Needs improvement"
                    >
                      <IconThumbDown className="h-4 w-4" />
                    </Button>
                  </>
                )}
              </div>
            </div>
            {feedbackIntent && !hasFeedback && (
              <MessageFeedbackForm
                intent={feedbackIntent}
                onCancel={() => setFeedbackIntent(null)}
                onSubmit={handleSubmitFeedback}
              />
            )}
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
  onSubmitFeedback,
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
          onSubmitFeedback={onSubmitFeedback}
        />
      );
    case 'system':
      return <SystemMessage message={message} />;
    default:
      return null;
  }
};
