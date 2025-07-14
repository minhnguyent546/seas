import { Button } from '@/components/ui/button';
import { CircularProgress } from '@mui/material';
import {
  IconFile,
  IconMicrophone,
  IconPhoto,
  IconSend,
} from '@tabler/icons-react';
import React, { useRef, useState } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading = false,
  placeholder = 'Ask me anything...',
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize the textarea based on content
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200,
      )}px`;
    }
  };

  const handleSendMessage = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="relative rounded-2xl border border-gray-200 bg-white p-2 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="flex w-full items-end gap-2">
        <div className="flex flex-1 flex-col">
          <textarea
            name="chat-input"
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="max-h-[200px] min-h-[40px] w-full resize-none border-0 bg-transparent px-2 py-2 text-base focus:outline-none focus:ring-0 dark:text-white"
            rows={1}
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            type="button"
            className="rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            aria-label="Upload image"
          >
            <IconPhoto size={20} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            type="button"
            className="rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            aria-label="Upload file"
          >
            <IconFile size={20} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            type="button"
            className="rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            aria-label="Voice input"
          >
            <IconMicrophone size={20} />
          </Button>
          <Button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-8 w-8 rounded-full bg-primary text-white hover:bg-primary-700"
            aria-label="Send message"
          >
            {isLoading ? (
              <CircularProgress size={16} color="inherit" />
            ) : (
              <IconSend size={16} />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
