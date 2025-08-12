import { useLanguage } from '@/hooks/useLanguage';
import {
  IconBooks,
  IconBuildingCommunity,
  IconCalendarEvent,
  IconCash,
  IconFileText,
  IconReceipt2,
} from '@tabler/icons-react';
import React from 'react';

interface RecommendedQuestionsProps {
  onQuestionClick: (question: string) => void;
}

export const RecommendedQuestions: React.FC<RecommendedQuestionsProps> = ({
  onQuestionClick,
}) => {
  const { t } = useLanguage();

  const questions = [
    {
      textKey: 'chat.recommendedQuestions.admissionRequirements',
      icon: <IconFileText className="h-6 w-6 text-primary" />,
    },
    {
      textKey: 'chat.recommendedQuestions.scholarships',
      icon: <IconCash className="h-6 w-6 text-secondary" />,
    },
    {
      textKey: 'chat.recommendedQuestions.programs',
      icon: <IconBooks className="h-6 w-6 text-tertiary" />,
    },
    {
      textKey: 'chat.recommendedQuestions.campusLife',
      icon: <IconBuildingCommunity className="h-6 w-6 text-primary" />,
    },
    {
      textKey: 'chat.recommendedQuestions.tuitionFees',
      icon: <IconReceipt2 className="h-6 w-6 text-secondary" />,
    },
    {
      textKey: 'chat.recommendedQuestions.applicationDeadline',
      icon: <IconCalendarEvent className="h-6 w-6 text-tertiary" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {questions.map((question) => {
        const questionText = t(question.textKey);
        return (
          <button
            key={question.textKey}
            type="button"
            className="group flex cursor-pointer items-center gap-4 rounded-xl border border-gray-200 bg-white p-3 text-left transition-all duration-200 ease-in-out hover:scale-[1.02] hover:bg-gray-50 hover:shadow-md dark:border-gray-700 dark:bg-gray-800/50 dark:hover:border-gray-600 dark:hover:bg-gray-800"
            onClick={() => onQuestionClick(questionText)}
          >
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100 shadow-sm dark:bg-gray-900">
              {question.icon}
            </div>
            <p className="flex-1 text-sm font-medium text-gray-700 dark:text-gray-200">
              {questionText}
            </p>
          </button>
        );
      })}
    </div>
  );
};
