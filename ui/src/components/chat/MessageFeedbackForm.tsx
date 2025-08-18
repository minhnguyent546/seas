import type { ChatMessageFeedbackType } from '@/client/types.gen';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useLanguage } from '@/hooks/useLanguage';
import { IconX } from '@tabler/icons-react';
import React, { useEffect, useRef, useState } from 'react';

interface MessageFeedbackFormProps {
  intent: 'like' | 'dislike';
  onCancel: () => void;
  onSubmit: (payload: {
    feedback: ChatMessageFeedbackType;
    detail?: string;
  }) => void;
}

interface FeedbackOption {
  value: ChatMessageFeedbackType;
  labelKey: string;
}

const LIKE_OPTIONS: FeedbackOption[] = [
  { value: 'LIKE_HELPFUL_ANSWER', labelKey: 'feedback.like.helpfulAnswer' },
  {
    value: 'LIKE_ACCURATE_INFORMATION',
    labelKey: 'feedback.like.accurateInformation',
  },
];

const DISLIKE_OPTIONS: FeedbackOption[] = [
  { value: 'DISLIKE_NOT_RELEVANT', labelKey: 'feedback.dislike.notRelevant' },
  {
    value: 'DISLIKE_INCORRECT_INFORMATION',
    labelKey: 'feedback.dislike.incorrectInformation',
  },
  {
    value: 'DISLIKE_INCOMPLETE_ANSWER',
    labelKey: 'feedback.dislike.incompleteAnswer',
  },
  { value: 'DISLIKE_OTHER', labelKey: 'feedback.dislike.other' },
];

export const MessageFeedbackForm: React.FC<MessageFeedbackFormProps> = ({
  intent,
  onCancel,
  onSubmit,
}) => {
  const { t } = useLanguage();
  const options = intent === 'like' ? LIKE_OPTIONS : DISLIKE_OPTIONS;
  const [selected, setSelected] = useState<ChatMessageFeedbackType>(
    options[0].value,
  );
  const [detail, setDetail] = useState('');
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      formRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'end',
        inline: 'nearest',
      });
    });
    return () => cancelAnimationFrame(raf);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ feedback: selected, detail: detail.trim() || undefined });
  };

  return (
    <form
      ref={formRef}
      onSubmit={handleSubmit}
      className="relative mt-2 rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/40"
    >
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="absolute right-1 top-1 h-8 w-8 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 cursor-pointer"
        onClick={onCancel}
        title={t('common.close')}
        aria-label={t('common.close')}
      >
        <IconX className="h-4 w-4" />
      </Button>
      <div className="flex flex-col gap-2">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
            {t('feedback.reason')}
          </label>
          <select
            value={selected}
            onChange={(e) =>
              setSelected(e.target.value as ChatMessageFeedbackType)
            }
            className="h-10 rounded-lg border border-gray-300 bg-white px-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary dark:border-gray-700 dark:bg-gray-900 dark:text-gray-50"
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {t(opt.labelKey)}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
            {t('feedback.detailsOptional')}
          </label>
          <Textarea
            placeholder={t('feedback.detailsPlaceholder')}
            value={detail}
            onChange={(e) => setDetail(e.target.value)}
            className="min-h-[72px]"
          />
        </div>
        <div className="flex items-center gap-2 pt-2 justify-end">
          <Button
            type="button"
            variant="ghost"
            size="md"
            className="cursor-pointer"
            onClick={onCancel}
          >
            {t('common.cancel')}
          </Button>
          <Button type="submit" size="md" className="cursor-pointer">
            {t('common.submit')}
          </Button>
        </div>
      </div>
    </form>
  );
};
