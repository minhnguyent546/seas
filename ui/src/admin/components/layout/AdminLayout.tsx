import { AdminSidebar } from '@/admin/components/layout/AdminSidebar';
import { Outlet } from '@tanstack/react-router';
import React, { useState } from 'react';

interface AdminLayoutProps {
  children?: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div
        className={`transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-16'
        }`}
        style={{ minWidth: sidebarOpen ? '256px' : '64px' }}
      >
        <AdminSidebar isCollapsed={!sidebarOpen} onToggle={toggleSidebar} />
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Main content */}
        <main className="flex-1 overflow-y-auto bg-white dark:bg-gray-800">
          <div className="p-6">{children || <Outlet />}</div>
        </main>
      </div>
    </div>
  );
};
