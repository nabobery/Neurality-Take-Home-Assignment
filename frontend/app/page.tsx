import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import ThemeToggle from './components/ThemeToggle';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 transition-colors">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Document Chat Interface
          </h1>
          <ThemeToggle />
        </div>
        <DocumentUpload />
        <div className="mt-8">
          <ChatInterface />
        </div>
      </div>
    </main>
  );
}