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
      <div className="flex flex-1 flex-col h-full">
        {/* Chat container */}
        <div className="flex-1 min-h-0">
          <ChatContainer userName={user.name.split(' ')[0]} />
        </div>
      </div>
    </div>
  );
}

export default App;
