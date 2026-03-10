import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './lib/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import SearchPage from './pages/SearchPage';
import DatasetsPage from './pages/DatasetsPage';
import CollectionsPage from './pages/CollectionsPage';
import CollectionDetailPage from './pages/CollectionDetailPage';
import LoginPage from './pages/LoginPage';
import PricingPage from './pages/PricingPage';
import AccountPage from './pages/AccountPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import CookiePage from './pages/CookiePage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/datasets" element={<DatasetsPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/cookies" element={<CookiePage />} />
            <Route
              path="/collections"
              element={
                <ProtectedRoute>
                  <CollectionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/collections/:id"
              element={
                <ProtectedRoute>
                  <CollectionDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/account"
              element={
                <ProtectedRoute>
                  <AccountPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  );
}
