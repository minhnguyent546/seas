import { ChatContainer } from '@/components/chat/ChatContainer';
import { Sidebar } from '@/components/layout/Sidebar';
import { Loading } from '@/components/ui/loading';
import useAuth from '@/hooks/useAuth';
import { useState } from 'react';

export function Chat() {
  const { user } = useAuth();
  const [testUser] = useState({
    id: '1',
    name: 'Test user',
    image: undefined,
  });

  const handleNewChat = () => {
    console.log('New chat created');
    // Implementation would reset the current chat or create a new one
  };

  const handleSettings = () => {
    console.log('Settings clicked');
    // Implementation would open settings panel
  };

  if (!user) {
    return <Loading message="Loading..." />;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-gray-950">
      {/* Sidebar */}
      <Sidebar
        onNewChat={handleNewChat}
        onSettingsClick={handleSettings}
        userName={user.full_name || user.email || 'User'}
        userAvatar={testUser.image}
      />

      {/* Main content */}
      <div className="flex flex-1 flex-col h-full">
        {/* Chat container */}
        <div className="flex-1 min-h-0">
          <ChatContainer
            userName={(user.full_name || user.email || 'User').split(' ')[0]}
          />
        </div>
      </div>
    </div>
  );
}
