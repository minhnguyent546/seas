import { useEffect, useRef, useState } from 'react';

export const useTypingEffect = (content: string, isLastMessage: boolean) => {
  const [displayText, setDisplayText] = useState('');
  const timeoutRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!content) {
      setDisplayText('');
      return;
    }

    // Only apply typing effect to the last message
    if (isLastMessage && content.length > displayText.length) {
      const typeText = () => {
        setDisplayText((prev) => {
          if (prev.length < content.length) {
            // Type multiple characters at once for faster effect
            const charsToAdd = Math.min(10, content.length - prev.length);
            return content.slice(0, prev.length + charsToAdd);
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
      setDisplayText(content);
    }

    return () => {
      if (timeoutRef.current !== undefined) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [content, isLastMessage, displayText.length]);

  return displayText;
};
