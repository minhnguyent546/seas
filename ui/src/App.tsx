import { ChatContainer } from '@/components/chat/ChatContainer';
import { Sidebar } from '@/components/layout/Sidebar';
import { useState } from 'react';
import './App.css';

function App() {
  const [user] = useState({
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

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-gray-950">
      {/* Sidebar */}
      <Sidebar
        onNewChat={handleNewChat}
        onSettingsClick={handleSettings}
        userName={user.name}
        userAvatar={user.image}
      />

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-gray-200 px-6 py-3 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-orange-500">SEAS-4</span>
          </div>
          <div className="flex items-center gap-2">
            <button className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
              Control
            </button>
          </div>
        </header>

        {/* Chat container */}
        <ChatContainer userName={user.name.split(' ')[0]} />
      </div>
    </div>
  );
}

export default App;
