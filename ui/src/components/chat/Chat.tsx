import { ChatContainer } from '@/components/chat/ChatContainer';
import { UserControls } from '@/components/chat/UserControls';
import { Sidebar } from '@/components/layout/Sidebar';
import { Loading } from '@/components/ui/loading';
import useAuth from '@/hooks/useAuth';

export function Chat() {
  const { user } = useAuth();

  const handleNewChat = () => {
    console.log('New chat created');
    // Implementation would reset the current chat or create a new one
  };

  if (!user) {
    return <Loading message="Loading..." />;
  }

  const userName = user.full_name || user.email || 'User';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-gray-950 relative">
      {/* User Controls (Language Toggle + User Avatar) in top right corner */}
      <UserControls />

      {/* Sidebar */}
      <Sidebar onNewChat={handleNewChat} />

      {/* Main content */}
      <div className="flex flex-1 flex-col h-full">
        {/* Chat container */}
        <div className="flex-1 min-h-0">
          <ChatContainer userName={userName.split(' ')[0]} />
        </div>
      </div>
    </div>
  );
}
