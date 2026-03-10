import { Navigate } from 'react-router-dom';
import { useAuth } from '../lib/AuthContext';
import { supabase } from '../lib/supabase';

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  // If Supabase isn't configured, allow access (dev mode)
  if (!supabase) return children;

  if (loading) {
    return <div className="mt-16 text-center text-gray-500">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
