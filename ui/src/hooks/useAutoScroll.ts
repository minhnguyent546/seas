import { useEffect, useRef } from 'react';

export const useAutoScroll = <T, E extends HTMLElement = HTMLDivElement>(
  dependency: T,
) => {
  const scrollRef = useRef<E>(null);

  const scrollToBottom = () => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToLastElement = () => {
    const container = scrollRef.current?.parentElement;
    if (container) {
      const lastChild = container.lastElementChild as HTMLElement;
      if (lastChild && lastChild !== scrollRef.current) {
        lastChild.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [dependency]);

  return { scrollRef, scrollToBottom, scrollToLastElement };
};
