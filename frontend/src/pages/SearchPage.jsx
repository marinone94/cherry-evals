import { useState, useEffect } from 'react';
import { searchKeyword, listCollections, addExamplesToCollection, createCollection } from '../lib/api';
import ExampleCard from '../components/ExampleCard';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState('');
  const [addedIds, setAddedIds] = useState(new Set());
  const [showNewColl, setShowNewColl] = useState(false);
  const [newCollName, setNewCollName] = useState('');

  useEffect(() => {
    listCollections()
      .then((data) => setCollections(data.collections || []))
      .catch(() => {});
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchKeyword(query.trim(), { limit: 50 });
      setResults(data.results || []);
      setTotal(data.total || 0);
      setAddedIds(new Set());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (exampleId) => {
    if (!selectedCollection) return;
    try {
      await addExamplesToCollection(parseInt(selectedCollection), [exampleId]);
      setAddedIds((prev) => new Set([...prev, exampleId]));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateCollection = async () => {
    if (!newCollName.trim()) return;
    try {
      const coll = await createCollection(newCollName.trim());
      setCollections((prev) => [coll, ...prev]);
      setSelectedCollection(String(coll.id));
      setNewCollName('');
      setShowNewColl(false);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Search Examples</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search questions and answers..."
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-red-500 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-red-600 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Collection selector */}
      <div className="flex items-center gap-2 mb-4 text-sm">
        <span className="text-gray-500">Add to:</span>
        <select
          value={selectedCollection}
          onChange={(e) => setSelectedCollection(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
        >
          <option value="">Select collection...</option>
          {collections.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {showNewColl ? (
          <div className="flex gap-1">
            <input
              type="text"
              value={newCollName}
              onChange={(e) => setNewCollName(e.target.value)}
              placeholder="Collection name"
              className="border border-gray-300 rounded px-2 py-1 text-sm"
              onKeyDown={(e) => e.key === 'Enter' && handleCreateCollection()}
            />
            <button
              onClick={handleCreateCollection}
              className="text-green-600 hover:text-green-800 text-sm font-medium"
            >
              Create
            </button>
            <button
              onClick={() => setShowNewColl(false)}
              className="text-gray-400 hover:text-gray-600 text-sm"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowNewColl(true)}
            className="text-red-500 hover:text-red-700 text-sm font-medium"
          >
            + New
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-2 rounded-lg mb-4 text-sm">{error}</div>
      )}

      {total > 0 && (
        <p className="text-sm text-gray-500 mb-3">
          Showing {results.length} of {total} results
        </p>
      )}

      <div className="space-y-3">
        {results.map((example) => (
          <ExampleCard
            key={example.id}
            example={example}
            actions={
              selectedCollection && (
                <button
                  onClick={() => handleAdd(example.id)}
                  disabled={addedIds.has(example.id)}
                  className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                    addedIds.has(example.id)
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-50 text-red-600 hover:bg-red-100'
                  }`}
                >
                  {addedIds.has(example.id) ? 'Added' : '+ Add'}
                </button>
              )
            }
          />
        ))}
      </div>

      {!loading && results.length === 0 && query && (
        <p className="text-center text-gray-400 py-12">No results found.</p>
      )}

      {!query && (
        <div className="text-center text-gray-400 py-16">
          <p className="text-lg mb-1">Search evaluation datasets</p>
          <p className="text-sm">Try searching for "math", "capital", or "photosynthesis"</p>
        </div>
      )}
    </div>
  );
}
