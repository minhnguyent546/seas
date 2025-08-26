import { Button } from '@/components/ui/button';
import {
  IconBell,
  IconDatabase,
  IconServer,
  IconShield,
} from '@tabler/icons-react';
import React, { useState } from 'react';

interface SettingsSectionProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const SettingsSection: React.FC<SettingsSectionProps> = ({
  title,
  description,
  icon,
  children,
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="text-gray-400 dark:text-gray-500">{icon}</div>
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            {title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {description}
          </p>
        </div>
      </div>
      {children}
    </div>
  );
};

interface SettingItemProps {
  label: string;
  description?: string;
  children: React.ReactNode;
}

const SettingItem: React.FC<SettingItemProps> = ({
  label,
  description,
  children,
}) => {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-900 dark:text-white">
          {label}
        </div>
        {description && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {description}
          </div>
        )}
      </div>
      <div className="ml-4">{children}</div>
    </div>
  );
};

type Settings = {
  maintenanceMode: boolean;
  userRegistration: boolean;
  emailNotifications: boolean;
  systemNotifications: boolean;
  dataRetention: string; // days
  maxSessionLength: string; // minutes
  apiRateLimit: string; // rpm
  backupEnabled: boolean;
};

type BooleanKeys<T> = {
  [K in keyof T]-?: T[K] extends boolean ? K : never;
}[keyof T];
type StringKeys<T> = {
  [K in keyof T]-?: T[K] extends string ? K : never;
}[keyof T];

export const AdminSettings: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    maintenanceMode: false,
    userRegistration: true,
    emailNotifications: true,
    systemNotifications: true,
    dataRetention: '90',
    maxSessionLength: '60',
    apiRateLimit: '1000',
    backupEnabled: true,
  });

  const handleToggle = (key: BooleanKeys<Settings>) => {
    setSettings((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleInputChange = (key: StringKeys<Settings>, value: string) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSave = () => {
    // TODO: Implement save settings functionality
    console.log('Save settings:', settings);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          System Settings
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Configure system-wide settings and preferences
        </p>
      </div>

      {/* Server Settings */}
      <SettingsSection
        title="Server Configuration"
        description="Core server and system settings"
        icon={<IconServer size={24} />}
      >
        <div className="space-y-0">
          <SettingItem
            label="Maintenance Mode"
            description="Enable maintenance mode to prevent user access"
          >
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.maintenanceMode}
                onChange={() => handleToggle('maintenanceMode')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
            </label>
          </SettingItem>

          <SettingItem
            label="User Registration"
            description="Allow new users to register accounts"
          >
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.userRegistration}
                onChange={() => handleToggle('userRegistration')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
            </label>
          </SettingItem>

          <SettingItem
            label="API Rate Limit"
            description="Maximum requests per minute per user"
          >
            <input
              type="number"
              value={settings.apiRateLimit}
              onChange={(e) =>
                handleInputChange('apiRateLimit', e.target.value)
              }
              min={0}
              step={1}
              inputMode="numeric"
              className="w-24 px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            />
          </SettingItem>
        </div>
      </SettingsSection>

      {/* Database Settings */}
      <SettingsSection
        title="Database & Storage"
        description="Data management and storage configuration"
        icon={<IconDatabase size={24} />}
      >
        <div className="space-y-0">
          <SettingItem
            label="Data Retention Period"
            description="Days to keep chat history and logs"
          >
            <select
              value={settings.dataRetention}
              onChange={(e) =>
                handleInputChange('dataRetention', e.target.value)
              }
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            >
              <option value="30">30 days</option>
              <option value="60">60 days</option>
              <option value="90">90 days</option>
              <option value="180">180 days</option>
              <option value="365">1 year</option>
              <option value="0">Never delete</option>
            </select>
          </SettingItem>

          <SettingItem
            label="Automatic Backups"
            description="Enable daily automatic database backups"
          >
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.backupEnabled}
                onChange={() => handleToggle('backupEnabled')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
            </label>
          </SettingItem>
        </div>
      </SettingsSection>

      {/* Security Settings */}
      <SettingsSection
        title="Security & Authentication"
        description="Security policies and authentication settings"
        icon={<IconShield size={24} />}
      >
        <div className="space-y-0">
          <SettingItem
            label="Max Session Length"
            description="Maximum session duration in minutes"
          >
            <input
              type="number"
              value={settings.maxSessionLength}
              onChange={(e) =>
                handleInputChange('maxSessionLength', e.target.value)
              }
              min={0}
              step={1}
              inputMode="numeric"
              className="w-24 px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            />
          </SettingItem>
        </div>
      </SettingsSection>

      {/* Notification Settings */}
      <SettingsSection
        title="Notifications"
        description="Email and system notification preferences"
        icon={<IconBell size={24} />}
      >
        <div className="space-y-0">
          <SettingItem
            label="Email Notifications"
            description="Send email notifications for important events"
          >
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.emailNotifications}
                onChange={() => handleToggle('emailNotifications')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
            </label>
          </SettingItem>

          <SettingItem
            label="System Notifications"
            description="Show system status and alert notifications"
          >
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.systemNotifications}
                onChange={() => handleToggle('systemNotifications')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
            </label>
          </SettingItem>
        </div>
      </SettingsSection>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} className="px-6" type="button">
          Save Changes
        </Button>
      </div>
    </div>
  );
};
