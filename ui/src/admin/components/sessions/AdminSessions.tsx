import { Button } from '@/components/ui/button';
import {
  IconDownload,
  IconEye,
  IconSearch,
  IconTrash,
} from '@tabler/icons-react';
import React, { useState } from 'react';

interface ChatSession {
  id: string;
  userId: string;
  userName: string;
  title: string;
  messageCount: number;
  createdAt: string;
  lastActivity: string;
  status: 'active' | 'completed' | 'abandoned';
}

interface SessionTableProps {
  sessions: ChatSession[];
  onView: (session: ChatSession) => void;
  onDelete: (session: ChatSession) => void;
  onExport: (session: ChatSession) => void;
}

const SessionTable: React.FC<SessionTableProps> = ({
  sessions,
  onView,
  onDelete,
  onExport,
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Session
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              User
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Messages
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
              Last Activity
            </th>
            <th className="relative px-6 py-3">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {sessions.map((session) => (
            <tr
              key={session.id}
              className="hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {session.title}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    ID: {session.id}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="h-8 w-8 flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                      <span className="text-xs font-medium text-white">
                        {session.userName.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="ml-3">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {session.userName}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {session.userId}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                {session.messageCount}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    session.status === 'active'
                      ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                      : session.status === 'completed'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  {session.status}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {session.lastActivity}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onView(session)}
                    className="h-8 w-8"
                    title="View session"
                  >
                    <IconEye size={16} />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onExport(session)}
                    className="h-8 w-8"
                    title="Export session"
                  >
                    <IconDownload size={16} />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(session)}
                    className="h-8 w-8 text-red-600 hover:text-red-900"
                    title="Delete session"
                  >
                    <IconTrash size={16} />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export const AdminSessions: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Mock data - replace with real data from API
  const mockSessions: ChatSession[] = [
    {
      id: 'sess_1',
      userId: 'user_1',
      userName: 'John Doe',
      title: 'Help with React components',
      messageCount: 15,
      createdAt: '2024-01-20',
      lastActivity: '2 hours ago',
      status: 'active',
    },
    {
      id: 'sess_2',
      userId: 'user_2',
      userName: 'Jane Smith',
      title: 'Database optimization question',
      messageCount: 8,
      createdAt: '2024-01-19',
      lastActivity: '1 day ago',
      status: 'completed',
    },
    {
      id: 'sess_3',
      userId: 'user_3',
      userName: 'Bob Johnson',
      title: 'API integration help',
      messageCount: 3,
      createdAt: '2024-01-18',
      lastActivity: '3 days ago',
      status: 'abandoned',
    },
  ];

  const filteredSessions = mockSessions.filter((session) => {
    const matchesSearch =
      session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' || session.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const handleViewSession = (session: ChatSession) => {
    // TODO: Implement view session functionality
    console.log('View session:', session);
  };

  const handleDeleteSession = (session: ChatSession) => {
    // TODO: Implement delete session functionality
    console.log('Delete session:', session);
  };

  const handleExportSession = (session: ChatSession) => {
    // TODO: Implement export session functionality
    console.log('Export session:', session);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Chat Sessions
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Monitor and manage all chat sessions in the system
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {mockSessions.filter((s) => s.status === 'active').length}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Active Sessions
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {mockSessions.reduce((sum, s) => sum + s.messageCount, 0)}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Total Messages
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {mockSessions.length}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Total Sessions
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <IconSearch size={16} className="text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search sessions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            />
          </div>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="block border border-gray-300 dark:border-gray-600 rounded-md py-2 px-3 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="abandoned">Abandoned</option>
        </select>
      </div>

      {/* Sessions Table */}
      <SessionTable
        sessions={filteredSessions}
        onView={handleViewSession}
        onDelete={handleDeleteSession}
        onExport={handleExportSession}
      />

      {/* Pagination (placeholder) */}
      <div className="flex items-center justify-between border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 rounded-lg">
        <div className="flex-1 flex justify-between sm:hidden">
          <Button variant="ghost">Previous</Button>
          <Button variant="ghost">Next</Button>
        </div>
        <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              Showing <span className="font-medium">1</span> to{' '}
              <span className="font-medium">{filteredSessions.length}</span> of{' '}
              <span className="font-medium">{filteredSessions.length}</span>{' '}
              results
            </p>
          </div>
          <div className="flex space-x-2">
            <Button variant="ghost">Previous</Button>
            <Button variant="ghost">Next</Button>
          </div>
        </div>
      </div>
    </div>
  );
};
