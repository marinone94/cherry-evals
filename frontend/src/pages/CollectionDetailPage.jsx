import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getCollection,
  listCollectionExamples,
  removeExampleFromCollection,
  exportCollection,
} from '../lib/api';

export default function CollectionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [collection, setCollection] = useState(null);
  const [examples, setExamples] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);

  const load = async () => {
    try {
      const [coll, exData] = await Promise.all([
        getCollection(id),
        listCollectionExamples(id),
      ]);
      setCollection(coll);
      setExamples(exData.examples || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleRemove = async (exampleId) => {
    try {
      await removeExampleFromCollection(id, exampleId);
      setExamples((prev) => prev.filter((e) => e.id !== exampleId));
      setCollection((prev) => prev && { ...prev, example_count: prev.example_count - 1 });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);
    setError(null);
    try {
      await exportCollection(id, format);
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting(false);
    }
  };

  if (loading) return <p className="text-gray-400 py-12 text-center">Loading...</p>;
  if (!collection) return <p className="text-red-600 py-12 text-center">Collection not found</p>;

  return (
    <div>
      <button
        onClick={() => navigate('/collections')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block"
      >
        &larr; Back to collections
      </button>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{collection.name}</h1>
          {collection.description && (
            <p className="text-gray-500 mt-1">{collection.description}</p>
          )}
          <p className="text-sm text-gray-400 mt-1">
            {collection.example_count} example{collection.example_count !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="flex gap-2">
          {['json', 'jsonl', 'csv'].map((fmt) => (
            <button
              key={fmt}
              onClick={() => handleExport(fmt)}
              disabled={exporting || examples.length === 0}
              className="bg-white border border-gray-300 text-gray-700 px-3 py-1.5 rounded text-sm hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {fmt.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-2 rounded-lg mb-4 text-sm">{error}</div>
      )}

      {examples.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          <p>No examples in this collection yet.</p>
          <button
            onClick={() => navigate('/')}
            className="text-red-500 hover:text-red-700 mt-2 text-sm font-medium"
          >
            Go to Search to add examples
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {examples.map((ex) => (
            <div
              key={ex.id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 mb-1">{ex.question}</p>
                  {ex.answer && (
                    <p className="text-sm text-gray-600">
                      <span className="font-medium text-green-700">Answer:</span> {ex.answer}
                    </p>
                  )}
                  {ex.choices && ex.choices.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {ex.choices.map((c, i) => (
                        <span
                          key={i}
                          className={`inline-block px-2 py-0.5 text-xs rounded-full ${
                            c === ex.answer
                              ? 'bg-green-100 text-green-800 font-medium'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-gray-400 mt-2">ID: {ex.id}</p>
                </div>
                <button
                  onClick={() => handleRemove(ex.id)}
                  className="text-xs text-gray-300 hover:text-red-500 transition-colors flex-shrink-0"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
