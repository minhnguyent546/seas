import { SeasLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { ROUTE_PATHS } from '@/constants/routePaths';
import useAuth from '@/hooks/useAuth';
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
import { useLocation, useNavigate } from '@tanstack/react-router';
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
  const navigate = useNavigate();

  const handleClick = () => {
    navigate({ to });
  };

  return (
    <div
      onClick={handleClick}
      className={`flex items-center w-full ${
        isCollapsed ? 'justify-center px-0' : 'justify-start px-2'
      } py-1.5 rounded-xl transition-colors duration-200 cursor-pointer ${
        isActive
          ? 'bg-primary/15 text-primary dark:bg-primary/25 dark:text-primary-light'
          : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
      }`}
    >
      <div className="flex-shrink-0">{icon}</div>
      {!isCollapsed && (
        <span className="ml-3 text-sm font-medium">{label}</span>
      )}
    </div>
  );
};

export const AdminSidebar: React.FC<AdminSidebarProps> = ({
  isCollapsed,
  onToggle,
}) => {
  // const { t } = useLanguage(); // TODO: Add translations when needed
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const displayName = user?.full_name || user?.email || '';

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
    <div className="flex h-full flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => (window.location.href = ROUTE_PATHS.ADMIN.DASHBOARD)}
            className="h-6 w-6 rounded-md text-primary hover:text-primary/80 cursor-pointer"
            title={'SEAS'}
          >
            <SeasLogo size={32} className="text-primary" />
          </Button>
          {!isCollapsed && (
            <button
              type="button"
              onClick={() =>
                (window.location.href = ROUTE_PATHS.ADMIN.DASHBOARD)
              }
              className="text-lg font-semibold text-primary cursor-pointer text-left"
              title="SEAS"
            >
              SEAS
            </button>
          )}
        </div>
        {!isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="h-6 w-6 cursor-pointer rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            title="Collapse sidebar"
          >
            <IconChevronLeft size={20} />
          </Button>
        )}
      </div>
      {/* Welcome (expanded only) */}
      {!isCollapsed && (
        <div className="px-4 pb-2 text-xs text-gray-500 dark:text-gray-400">
          {`Welcome back, Admin${displayName ? ` ${displayName}` : ''}`}
        </div>
      )}
      {/* Expand button (collapsed only) */}
      {isCollapsed && (
        <div className="px-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="rounded-lg text-gray-700 dark:text-gray-300 cursor-pointer"
            aria-label="Expand sidebar"
            title="Expand sidebar"
          >
            <IconChevronsRight size={20} />
          </Button>
        </div>
      )}
      {/* Divider */}
      <div className="mx-4 border-t border-gray-200 dark:border-gray-700" />

      {/* Navigation */}
      <nav className={`flex-1 ${isCollapsed ? 'px-0' : 'px-4'} py-2`}>
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
        <div
          onClick={() => navigate({ to: ROUTE_PATHS.HOME })}
          className={`flex items-center w-full ${
            isCollapsed ? 'justify-center px-0' : 'justify-start px-2'
          } text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl py-1.5 mb-2 cursor-pointer`}
          title="Go to Chat"
        >
          <IconHome size={20} />
          {!isCollapsed && <span className="ml-3 text-sm">Chat</span>}
        </div>
        <Button
          variant="ghost"
          onClick={handleLogout}
          className={`flex items-center w-full cursor-pointer ${
            isCollapsed ? 'justify-center px-0' : 'justify-start px-2'
          } text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl`}
          title="Logout"
        >
          <IconLogout size={20} />
          {!isCollapsed && <span className="ml-3 text-sm">Logout</span>}
        </Button>
      </div>
    </div>
  );
};
