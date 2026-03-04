import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listDatasets } from '../lib/api';
import { taskTypeBadgeClasses } from '../lib/taskTypeColors';

// ---------------------------------------------------------------------------
// Skeleton card shown while datasets are loading
// ---------------------------------------------------------------------------
function SkeletonCard() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
      <div className="h-3 bg-gray-100 rounded w-full mb-1" />
      <div className="h-3 bg-gray-100 rounded w-4/5 mb-4" />
      <div className="flex items-center gap-2">
        <div className="h-5 bg-gray-200 rounded w-24" />
        <div className="h-4 bg-gray-100 rounded w-20" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// License badge — neutral styling; license text is usually short
// ---------------------------------------------------------------------------
function LicenseBadge({ license }) {
  if (!license) return null;
  return (
    <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded border border-gray-200">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-3 w-3"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      {license}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Derive a HuggingFace search URL from a dataset name.
// If the dataset already looks like an org/repo slug, link directly.
// ---------------------------------------------------------------------------
function huggingFaceUrl(name) {
  // e.g. "cais/mmlu" → direct dataset page
  if (name && /^[\w-]+\/[\w.-]+$/.test(name)) {
    return `https://huggingface.co/datasets/${name}`;
  }
  // Fall back to a search query
  return `https://huggingface.co/datasets?search=${encodeURIComponent(name || '')}`;
}

// ---------------------------------------------------------------------------
// Stats breakdown: show split counts and/or subject counts when available
// ---------------------------------------------------------------------------
function StatsBreakdown({ ds }) {
  const parts = [];

  if (ds.splits && typeof ds.splits === 'object') {
    const splitEntries = Object.entries(ds.splits);
    if (splitEntries.length > 0) {
      parts.push(
        <span key="splits" className="text-gray-500">
          Splits:{' '}
          {splitEntries
            .map(([k, v]) => `${k} (${(v || 0).toLocaleString()})`)
            .join(', ')}
        </span>
      );
    }
  }

  if (ds.subject_count != null && ds.subject_count > 0) {
    parts.push(
      <span key="subjects" className="text-gray-500">
        {ds.subject_count} subject{ds.subject_count !== 1 ? 's' : ''}
      </span>
    );
  }

  if (parts.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs mt-2 border-t border-gray-100 pt-2">
      {parts}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function DatasetsPage() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    listDatasets()
      .then((data) => setDatasets(data.datasets || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (error) {
    return <p className="text-red-600 py-12 text-center">{error}</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Datasets</h1>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : datasets.length === 0 ? (
        <p className="text-gray-400 text-center py-12">
          No datasets ingested yet. Run the CLI to ingest your first dataset.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((ds) => (
            <div
              key={ds.id}
              className="bg-white rounded-lg border border-gray-200 p-5 flex flex-col hover:shadow-sm transition-shadow"
            >
              {/* Header row: name + HuggingFace link */}
              <div className="flex items-start justify-between gap-2 mb-1">
                <h2 className="font-semibold text-gray-900 leading-snug">{ds.name}</h2>
                <a
                  href={huggingFaceUrl(ds.source || ds.name)}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="View on HuggingFace"
                  className="flex-shrink-0 text-gray-300 hover:text-yellow-500 transition-colors mt-0.5"
                  aria-label="View on HuggingFace"
                >
                  {/* HuggingFace logo (simplified face icon) */}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm-2.5 7a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm5 0a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm-5.5 5.5h6a.5.5 0 01.5.5v.5a3.5 3.5 0 01-7 0v-.5a.5.5 0 01.5-.5z" />
                  </svg>
                </a>
              </div>

              {/* Description */}
              {ds.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2 leading-snug">
                  {ds.description}
                </p>
              )}

              {/* Badges row */}
              <div className="flex flex-wrap items-center gap-2 text-xs mb-2">
                <span
                  className={`px-2 py-0.5 rounded font-medium ${taskTypeBadgeClasses(ds.task_type)}`}
                >
                  {ds.task_type}
                </span>
                <LicenseBadge license={ds.license} />
                <span className="text-gray-400">
                  {(ds.example_count || 0).toLocaleString()} examples
                </span>
              </div>

              {/* Stats breakdown (splits, subjects) */}
              <StatsBreakdown ds={ds} />

              {/* Spacer to push button to bottom */}
              <div className="flex-1" />

              {/* Browse Examples button */}
              <button
                type="button"
                onClick={() =>
                  navigate(`/?dataset=${encodeURIComponent(ds.name)}`)
                }
                className="mt-4 w-full text-center text-xs font-medium py-1.5 rounded-md border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
              >
                Browse Examples
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
