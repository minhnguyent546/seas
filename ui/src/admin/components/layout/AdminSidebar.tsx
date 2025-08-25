import { AdminSidebarFooter } from '@/admin/components/layout/AdminSidebarFooter';
import { AdminSidebarHeader } from '@/admin/components/layout/AdminSidebarHeader';
import { ROUTE_PATHS } from '@/constants/routePaths';
import {
  IconDashboard,
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
      } py-2.5 rounded-xl transition-colors duration-200 cursor-pointer ${
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

  return (
    <div className="flex h-full flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 rounded-xl">
      <AdminSidebarHeader isCollapsed={isCollapsed} onToggle={onToggle} />

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

      <AdminSidebarFooter isCollapsed={isCollapsed} />
    </div>
  );
};
