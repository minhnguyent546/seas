import { useCallback } from 'react';

export const useMessageActions = () => {
  const handleCopyMessage = useCallback(async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      // TODO: add toast notification here
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  }, []);

  const handleLikeMessage = useCallback((messageId: string) => {
    // TODO: implement like functionality
    console.log('Liked message:', messageId);
  }, []);

  const handleDislikeMessage = useCallback((messageId: string) => {
    // TODO: implement dislike functionality
    console.log('Disliked message:', messageId);
  }, []);

  return {
    handleCopyMessage,
    handleLikeMessage,
    handleDislikeMessage,
  };
};
