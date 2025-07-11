import React from 'react';
import { ImageIcon, FileIcon, MicrophoneIcon } from '@/components/icons';
import type { ChatFeature } from '@/types/chat';

interface ChatFeaturesProps {
  onFeatureClick: (feature: ChatFeature) => void;
}

const features: ChatFeature[] = [
  {
    id: 'upload-images',
    title: 'Upload Images',
    description: 'Upload images for quick processing',
    icon: <ImageIcon className="h-10 w-10 text-primary" />,
  },
  {
    id: 'generate-images',
    title: 'Generate Images',
    description: 'Create custom AI generated images from your ideas',
    icon: <ImageIcon className="h-10 w-10 text-tertiary" />,
  },
  {
    id: 'upload-files',
    title: 'Upload files',
    description: 'Easily manage and process various file types',
    icon: <FileIcon className="h-10 w-10 text-primary" />,
  },
  {
    id: 'voice-memo',
    title: 'Voice Memo',
    description: 'Upload or record voice memo to generate ideas',
    icon: <MicrophoneIcon className="h-10 w-10 text-tertiary" />,
  },
];

export const ChatFeatures: React.FC<ChatFeaturesProps> = ({ onFeatureClick }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {features.map((feature) => (
        <button
          key={feature.id}
          className="group flex cursor-pointer flex-col items-start rounded-2xl border border-gray-200 bg-gray-50 p-4 transition-all hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-900 dark:hover:bg-gray-800 hover:shadow-md"
          onClick={() => onFeatureClick(feature)}
        >
          <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-white p-2 shadow-sm dark:bg-gray-800">
            {feature.icon}
          </div>
          <div className="text-left">
            <h3 className="text-base font-medium">{feature.title}</h3>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {feature.description}
            </p>
          </div>
        </button>
      ))}
    </div>
  );
};
