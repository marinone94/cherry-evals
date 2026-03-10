import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAuth } from '../lib/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  // Already logged in
  if (user) {
    navigate('/');
    return null;
  }

  if (!supabase) {
    return (
      <div className="max-w-md mx-auto mt-16 p-6 bg-white rounded-lg border border-gray-200">
        <h1 className="text-xl font-bold mb-4">Authentication not configured</h1>
        <p className="text-gray-600">
          Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to enable auth.
        </p>
      </div>
    );
  }

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { error: authError } = isSignUp
        ? await supabase.auth.signUp({ email, password })
        : await supabase.auth.signInWithPassword({ email, password });

      if (authError) throw authError;

      if (isSignUp) {
        setError('Check your email for a confirmation link.');
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider) => {
    setError('');
    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: window.location.origin },
    });
    if (authError) setError(authError.message);
  };

  return (
    <div className="max-w-md mx-auto mt-16 p-6 bg-white rounded-lg border border-gray-200">
      <h1 className="text-xl font-bold mb-6">
        {isSignUp ? 'Create account' : 'Sign in'}
      </h1>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">{error}</div>
      )}

      <form onSubmit={handleEmailAuth} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
        </div>
        {isSignUp && (
          <p className="text-xs text-gray-500">
            By creating an account you agree to our{' '}
            <a href="/terms" className="text-red-500 underline">Terms of Service</a> and{' '}
            <a href="/privacy" className="text-red-500 underline">Privacy Policy</a>.
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 bg-red-500 text-white rounded-md hover:bg-red-600 disabled:opacity-50 font-medium"
        >
          {loading ? 'Loading...' : isSignUp ? 'Create account' : 'Sign in'}
        </button>
      </form>

      <div className="mt-4 flex items-center gap-3">
        <hr className="flex-1" />
        <span className="text-sm text-gray-500">or</span>
        <hr className="flex-1" />
      </div>

      <div className="mt-4 space-y-2">
        <button
          onClick={() => handleOAuth('google')}
          className="w-full py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm font-medium"
        >
          Continue with Google
        </button>
        <button
          onClick={() => handleOAuth('github')}
          className="w-full py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm font-medium"
        >
          Continue with GitHub
        </button>
      </div>

      <p className="mt-6 text-center text-sm text-gray-600">
        {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
        <button
          onClick={() => {
            setIsSignUp(!isSignUp);
            setError('');
          }}
          className="text-red-500 hover:text-red-600 font-medium"
        >
          {isSignUp ? 'Sign in' : 'Create account'}
        </button>
      </p>
    </div>
  );
}
