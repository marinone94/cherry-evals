import { useState, useEffect } from 'react';
import { listDatasets } from '../lib/api';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listDatasets()
      .then((data) => setDatasets(data.datasets || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-400 py-12 text-center">Loading datasets...</p>;
  if (error) return <p className="text-red-600 py-12 text-center">{error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Datasets</h1>

      {datasets.length === 0 ? (
        <p className="text-gray-400 text-center py-12">
          No datasets ingested yet. Run the CLI to ingest your first dataset.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((ds) => (
            <div key={ds.id} className="bg-white rounded-lg border border-gray-200 p-5">
              <h2 className="font-semibold text-gray-900 mb-1">{ds.name}</h2>
              {ds.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">{ds.description}</p>
              )}
              <div className="flex items-center gap-3 text-xs text-gray-400">
                <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                  {ds.task_type}
                </span>
                <span>{ds.example_count?.toLocaleString() || 0} examples</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
