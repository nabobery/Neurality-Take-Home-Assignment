import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-8">
          Document Chat Interface
        </h1>
        <DocumentUpload />
        <div className="mt-8">
          <ChatInterface />
        </div>
      </div>
    </main>
  );
}