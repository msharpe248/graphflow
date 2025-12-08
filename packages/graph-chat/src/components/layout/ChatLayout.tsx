import Header from './Header';
import Sidebar from '@/components/sidebar/Sidebar';
import ChatContainer from '@/components/chat/ChatContainer';

export default function ChatLayout() {
  return (
    <div className="h-screen flex flex-col">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main chat area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <ChatContainer />
        </main>
      </div>
    </div>
  );
}
