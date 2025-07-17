import { useEffect, useRef, useState } from 'react';

export const useTypingEffect = (content: string, isLastMessage: boolean) => {
  const [displayText, setDisplayText] = useState('');
  const timeoutRef = useRef<number | undefined>(undefined);
  const currentIndexRef = useRef(0);
  const isTypingRef = useRef(false);

  useEffect(() => {
    // Clear any existing timeout
    if (timeoutRef.current !== undefined) {
      clearTimeout(timeoutRef.current);
    }

    if (!content) {
      setDisplayText('');
      currentIndexRef.current = 0;
      isTypingRef.current = false;
      return;
    }

    // For non-last messages, show immediately
    if (!isLastMessage) {
      setDisplayText(content);
      currentIndexRef.current = content.length;
      isTypingRef.current = false;
      return;
    }

    // If content is shorter than current display, show immediately
    if (content.length <= displayText.length) {
      setDisplayText(content);
      currentIndexRef.current = content.length;
      isTypingRef.current = false;
      return;
    }

    // Start typing effect for last message
    currentIndexRef.current = displayText.length;
    isTypingRef.current = true;

    const typeText = () => {
      if (!isTypingRef.current) return;

      const charsToAdd = Math.min(10, content.length - currentIndexRef.current);

      if (charsToAdd > 0) {
        currentIndexRef.current += charsToAdd;
        setDisplayText(content.slice(0, currentIndexRef.current));

        // Continue typing if there's more content
        if (currentIndexRef.current < content.length) {
          timeoutRef.current = window.setTimeout(typeText, 5);
        } else {
          isTypingRef.current = false;
        }
      } else {
        isTypingRef.current = false;
      }
    };

    // Start the typing animation
    timeoutRef.current = window.setTimeout(typeText, 5);

    return () => {
      if (timeoutRef.current !== undefined) {
        clearTimeout(timeoutRef.current);
      }
      isTypingRef.current = false;
    };
  }, [content, isLastMessage]);

  return displayText;
};
