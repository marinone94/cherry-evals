import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../lib/AuthContext';

const navItems = [
  { path: '/', label: 'Search' },
  { path: '/datasets', label: 'Datasets' },
  { path: '/collections', label: 'Collections' },
  { path: '/pricing', label: 'Pricing' },
];

export default function Layout({ children }) {
  const { user, loading } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <NavLink to="/" className="flex items-center gap-2 font-bold text-lg text-gray-900">
              <span className="text-red-500">&#127826;</span>
              Cherry Evals
            </NavLink>
            <div className="flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-red-50 text-red-600'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}

              {!loading && (
                <>
                  {user ? (
                    <NavLink
                      to="/account"
                      className={({ isActive }) =>
                        `ml-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-red-50 text-red-600'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }`
                      }
                    >
                      Account
                    </NavLink>
                  ) : (
                    <NavLink
                      to="/login"
                      className="ml-2 px-3 py-1.5 bg-red-500 text-white rounded-md text-sm font-medium hover:bg-red-600 transition-colors"
                    >
                      Sign in
                    </NavLink>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">{children}</main>
      <footer className="border-t border-gray-200 bg-white mt-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
          <span>Elastic License 2.0</span>
          <div className="flex gap-4">
            <Link to="/terms" className="hover:text-gray-700">Terms</Link>
            <Link to="/privacy" className="hover:text-gray-700">Privacy</Link>
            <Link to="/cookies" className="hover:text-gray-700">Cookies</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
