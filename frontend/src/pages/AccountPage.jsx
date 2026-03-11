import { useEffect, useState } from 'react';
import { useAuth } from '../lib/AuthContext';
import { getAccount, listApiKeys, createApiKey, revokeApiKey } from '../lib/api';

const TIER_BADGE = {
  free: 'bg-gray-100 text-gray-600',
  pro: 'bg-red-100 text-red-700',
  ultra: 'bg-purple-100 text-purple-700',
};

function trialDaysLeft(trialEndsAt) {
  if (!trialEndsAt) return 0;
  const diff = new Date(trialEndsAt) - new Date();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

export default function AccountPage() {
  const { user, signOut } = useAuth();
  const [account, setAccount] = useState(null);
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getAccount().catch(() => null),
      listApiKeys().catch(() => []),
    ]).then(([acc, keys]) => {
      setAccount(acc);
      setApiKeys(Array.isArray(keys) ? keys : []);
      setLoading(false);
    });
  }, []);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    setError('');
    setCreatedKey(null);
    try {
      const result = await createApiKey(newKeyName || 'Default');
      setCreatedKey(result.key);
      setNewKeyName('');
      // Refresh list
      const keys = await listApiKeys();
      setApiKeys(Array.isArray(keys) ? keys : []);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRevoke = async (id) => {
    try {
      await revokeApiKey(id);
      setApiKeys(apiKeys.filter((k) => k.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="mt-8 text-center text-gray-500">Loading...</div>;
  }

  const daysLeft = account ? trialDaysLeft(account.trial_ends_at) : 0;
  const onTrial = account?.effective_tier === 'ultra' && account?.tier === 'free' && daysLeft > 0;
  const badgeTier = account?.effective_tier || account?.tier || 'free';
  const badgeColors = TIER_BADGE[badgeTier] || TIER_BADGE.free;

  return (
    <div className="max-w-2xl mx-auto mt-8 space-y-8">
      {/* Trial banner */}
      {onTrial && (
        <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg text-center text-sm text-purple-700">
          Ultra trial ends in {daysLeft} day{daysLeft !== 1 ? 's' : ''}
        </div>
      )}

      {/* Profile */}
      <section className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Profile</h2>
        {account ? (
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Email</dt>
              <dd className="text-gray-900">{account.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Plan</dt>
              <dd>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${badgeColors}`}
                >
                  {onTrial
                    ? 'FREE (Ultra trial)'
                    : badgeTier.toUpperCase()}
                </span>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Member since</dt>
              <dd className="text-gray-900">
                {new Date(account.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="text-gray-500 text-sm">Could not load account info.</p>
        )}
        <button
          onClick={signOut}
          className="mt-4 text-sm text-red-500 hover:text-red-600 font-medium"
        >
          Sign out
        </button>
      </section>

      {/* Usage */}
      {account?.usage && (
        <section className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Usage today</h2>
          <div className="space-y-3">
            <UsageBar
              label="Semantic searches"
              used={account.usage.semantic_searches_today}
              limit={account.usage.semantic_searches_limit}
            />
            <UsageBar
              label="LLM calls"
              used={account.usage.llm_calls_today}
              limit={account.usage.llm_calls_limit}
            />
          </div>
          <p className="mt-3 text-xs text-gray-400">
            Resets at {new Date(account.usage.quota_resets_at).toLocaleString()}
          </p>
        </section>
      )}

      {/* API Keys */}
      <section className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">API Keys</h2>

        {error && (
          <div className="mb-3 p-2 bg-red-50 text-red-700 rounded text-sm">{error}</div>
        )}

        {createdKey && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm font-medium text-green-800">
              Key created! Copy it now — you won&apos;t see it again.
            </p>
            <code className="block mt-1 text-xs bg-white p-2 rounded border font-mono break-all">
              {createdKey}
            </code>
          </div>
        )}

        <form onSubmit={handleCreateKey} className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Key name (optional)"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <button
            type="submit"
            className="px-4 py-1.5 bg-red-500 text-white rounded-md hover:bg-red-600 text-sm font-medium"
          >
            Create
          </button>
        </form>

        {apiKeys.length > 0 ? (
          <ul className="space-y-2">
            {apiKeys.map((k) => (
              <li
                key={k.id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded-md text-sm"
              >
                <div>
                  <span className="font-medium text-gray-900">{k.name}</span>
                  <span className="ml-2 text-gray-400 font-mono">{k.key_prefix}...</span>
                </div>
                <button
                  onClick={() => handleRevoke(k.id)}
                  className="text-red-500 hover:text-red-600 text-xs font-medium"
                >
                  Revoke
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-500">No API keys yet.</p>
        )}
      </section>
    </div>
  );
}

function UsageBar({ label, used, limit }) {
  const isUnlimited = limit === -1;
  const isBlocked = limit === 0;
  const pct = isUnlimited || isBlocked ? 0 : Math.min((used / limit) * 100, 100);

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="text-gray-500">
          {isBlocked
            ? 'Blocked (upgrade required)'
            : isUnlimited
              ? `${used} / unlimited`
              : `${used} / ${limit}`}
        </span>
      </div>
      {!isBlocked && !isUnlimited && (
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-400' : 'bg-green-500'
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}
