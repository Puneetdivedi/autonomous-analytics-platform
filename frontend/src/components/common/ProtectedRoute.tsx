import { ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import Spinner from './Spinner';

// Sign-in has been removed: a guest session is provisioned automatically by
// AuthProvider, so this simply waits for that bootstrap and then renders the app.
export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { loading } = useAuth();

  if (loading) {
    return <Spinner fullscreen label="Preparing your workspace..." />;
  }

  return <>{children}</>;
}
