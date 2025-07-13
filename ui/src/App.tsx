import type { ReactNode } from 'react';
import './App.css';

interface AppProps {
  children?: ReactNode;
}

/**
 * App component is now a simple wrapper component for global providers and settings
 * The actual routing is handled in main.tsx with RouterProvider from TanStack Router
 */
function App({ children }: AppProps) {
  return <>{children}</>;
}

export default App;
