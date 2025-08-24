import { Button } from '@/components/ui/button';
import { ROUTE_PATHS } from '@/constants/path_routes';
import {
  IconChevronLeft,
  IconChevronsRight,
  IconDashboard,
  IconHome,
  IconLogout,
  IconMessages,
  IconSettings,
  IconUsers,
} from '@tabler/icons-react';
import { Link, useLocation } from '@tanstack/react-router';
import React from 'react';

interface AdminSidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

interface SidebarItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  isCollapsed: boolean;
  isActive?: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  to,
  icon,
  label,
  isCollapsed,
  isActive = false,
}) => {
  return (
    <Link
      to={to}
      className={`flex items-center px-3 py-2 rounded-md transition-colors duration-200 ${
        isActive
          ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
      }`}
    >
      <div className="flex-shrink-0">{icon}</div>
      {!isCollapsed && (
        <span className="ml-3 text-sm font-medium">{label}</span>
      )}
    </Link>
  );
};

export const AdminSidebar: React.FC<AdminSidebarProps> = ({
  isCollapsed,
  onToggle,
}) => {
  // const { t } = useLanguage(); // TODO: Add translations when needed
  const location = useLocation();

  const menuItems = [
    {
      to: ROUTE_PATHS.ADMIN.DASHBOARD,
      icon: <IconDashboard size={20} />,
      label: 'Dashboard',
    },
    {
      to: ROUTE_PATHS.ADMIN.USERS,
      icon: <IconUsers size={20} />,
      label: 'Users',
    },
    {
      to: ROUTE_PATHS.ADMIN.SESSIONS,
      icon: <IconMessages size={20} />,
      label: 'Sessions',
    },
    {
      to: ROUTE_PATHS.ADMIN.SETTINGS,
      icon: <IconSettings size={20} />,
      label: 'Settings',
    },
  ];

  const handleLogout = () => {
    // TODO: Implement logout functionality
    console.log('Logout clicked');
  };

  return (
    <div className="flex h-full flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center">
          {!isCollapsed && (
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Admin Panel
            </h1>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className="h-8 w-8 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <IconChevronsRight size={18} />
          ) : (
            <IconChevronLeft size={18} />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-2">
        <div className="space-y-1">
          {menuItems.map((item) => (
            <SidebarItem
              key={item.to}
              to={item.to}
              icon={item.icon}
              label={item.label}
              isCollapsed={isCollapsed}
              isActive={location.pathname === item.to}
            />
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <Link
          to={ROUTE_PATHS.HOME}
          className={`flex items-center w-full text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md py-2 ${
            isCollapsed ? 'justify-center px-2' : 'justify-start px-3'
          } mb-2`}
          title="Go to Chat"
        >
          <IconHome size={20} />
          {!isCollapsed && <span className="ml-3 text-sm">Chat</span>}
        </Link>
        <Button
          variant="ghost"
          onClick={handleLogout}
          className={`flex items-center w-full text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 ${
            isCollapsed ? 'justify-center px-2' : 'justify-start px-3'
          }`}
          title="Logout"
        >
          <IconLogout size={20} />
          {!isCollapsed && <span className="ml-3 text-sm">Logout</span>}
        </Button>
      </div>
    </div>
  );
};
