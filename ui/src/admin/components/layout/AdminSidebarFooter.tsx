import { ROUTE_PATHS } from '@/constants/routePaths';
import useAuth from '@/hooks/useAuth';
import { IconHome, IconLogout } from '@tabler/icons-react';
import { useNavigate } from '@tanstack/react-router';
import React from 'react';

interface AdminSidebarFooterProps {
  isCollapsed: boolean;
}

export const AdminSidebarFooter: React.FC<AdminSidebarFooterProps> = ({
  isCollapsed,
}) => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="p-4 border-t border-gray-200 dark:border-gray-700">
      <div
        onClick={() => navigate({ to: ROUTE_PATHS.HOME })}
        className={`flex items-center w-full ${
          isCollapsed ? 'justify-center px-0' : 'justify-start px-2'
        } text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl py-2 mb-2 cursor-pointer`}
        title="Go to Chat"
      >
        <IconHome size={20} />
        {!isCollapsed && <span className="ml-3 text-sm">Chat</span>}
      </div>
      <div
        onClick={handleLogout}
        className={`flex items-center w-full cursor-pointer ${
          isCollapsed ? 'justify-center px-0' : 'justify-start px-2'
        } text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 rounded-xl py-2`}
        title="Logout"
      >
        <IconLogout size={20} />
        {!isCollapsed && <span className="ml-3 text-sm">Logout</span>}
      </div>
    </div>
  );
};
