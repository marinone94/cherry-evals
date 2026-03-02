import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listCollections, createCollection, deleteCollection } from '../lib/api';

export default function CollectionsPage() {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const load = () => {
    listCollections()
      .then((data) => setCollections(data.collections || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await createCollection(name.trim(), description.trim() || null);
      setName('');
      setDescription('');
      setShowCreate(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id, collName) => {
    if (!window.confirm(`Delete "${collName}"? This cannot be undone.`)) return;
    try {
      await deleteCollection(id);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p className="text-gray-400 py-12 text-center">Loading collections...</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Collections</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="bg-red-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-600 transition-colors"
        >
          {showCreate ? 'Cancel' : '+ New Collection'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-2 rounded-lg mb-4 text-sm">{error}</div>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Collection name"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-red-400"
            autoFocus
          />
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-red-400"
          />
          <button
            type="submit"
            className="bg-red-500 text-white px-4 py-1.5 rounded text-sm font-medium hover:bg-red-600"
          >
            Create
          </button>
        </form>
      )}

      {collections.length === 0 ? (
        <p className="text-gray-400 text-center py-12">
          No collections yet. Create one and start cherry-picking examples.
        </p>
      ) : (
        <div className="space-y-3">
          {collections.map((coll) => (
            <div
              key={coll.id}
              className="bg-white rounded-lg border border-gray-200 p-4 flex items-center justify-between hover:shadow-sm transition-shadow"
            >
              <Link to={`/collections/${coll.id}`} className="flex-1 min-w-0">
                <h2 className="font-semibold text-gray-900">{coll.name}</h2>
                {coll.description && (
                  <p className="text-sm text-gray-500 truncate">{coll.description}</p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  {coll.example_count} example{coll.example_count !== 1 ? 's' : ''}
                </p>
              </Link>
              <button
                onClick={() => handleDelete(coll.id, coll.name)}
                className="text-gray-300 hover:text-red-500 transition-colors ml-4 text-sm"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
