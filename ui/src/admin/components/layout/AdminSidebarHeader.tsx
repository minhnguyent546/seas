import { SeasLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { ROUTE_PATHS } from '@/constants/routePaths';
import useAuth from '@/hooks/useAuth';
import { IconChevronLeft, IconChevronsRight } from '@tabler/icons-react';
import React from 'react';

interface AdminSidebarHeaderProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

export const AdminSidebarHeader: React.FC<AdminSidebarHeaderProps> = ({
  isCollapsed,
  onToggle,
}) => {
  const { user } = useAuth();
  const displayName = user?.full_name || user?.email || '';

  return (
    <>
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
    </>
  );
};
