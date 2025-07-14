import { Chat } from '@/components/chat/Chat';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  return <Chat />;
}
