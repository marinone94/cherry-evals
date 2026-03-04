import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  searchKeyword,
  searchIntelligent,
  listCollections,
  addExamplesToCollection,
  createCollection,
  getSearchFacets,
} from '../lib/api';
import ExampleCard from '../components/ExampleCard';

export default function SearchPage() {
  const [searchParams] = useSearchParams();

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
  const [searchMode, setSearchMode] = useState('keyword');
  const [metadata, setMetadata] = useState(null);
  const [metaExpanded, setMetaExpanded] = useState(true);

  // Facets & filters
  const [facets, setFacets] = useState({ datasets: [], task_types: [], subjects: [] });
  const [filterDataset, setFilterDataset] = useState('');
  const [filterTaskType, setFilterTaskType] = useState('');

  // Bulk select
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkAdding, setBulkAdding] = useState(false);

  // Read ?dataset= query param from DatasetsPage "Browse Examples" link
  const presetDataset = searchParams.get('dataset') || '';

  // Load collections and initial facets on mount; apply any preset filter
  useEffect(() => {
    listCollections()
      .then((data) => setCollections(data.collections || []))
      .catch(() => {});
    getSearchFacets(null)
      .then((data) => setFacets(data))
      .catch(() => {});

    if (presetDataset) {
      setFilterDataset(presetDataset);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshFacets = useCallback((q) => {
    getSearchFacets(q || null)
      .then((data) => setFacets(data))
      .catch(() => {});
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setMetadata(null);
    try {
      const opts = {
        limit: 50,
        ...(filterDataset ? { dataset: filterDataset } : {}),
        ...(filterTaskType ? { task_type: filterTaskType } : {}),
      };
      if (searchMode === 'intelligent') {
        const data = await searchIntelligent(query.trim(), { limit: 50 });
        setResults(data.results || []);
        setTotal(data.total || 0);
        setMetadata(data.metadata || null);
      } else {
        const data = await searchKeyword(query.trim(), opts);
        setResults(data.results || []);
        setTotal(data.total || 0);
      }
      setAddedIds(new Set());
      setSelectedIds(new Set());
      refreshFacets(query.trim());
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

  const handleBulkAdd = async () => {
    if (!selectedCollection || selectedIds.size === 0) return;
    setBulkAdding(true);
    setError(null);
    try {
      const ids = Array.from(selectedIds);
      await addExamplesToCollection(parseInt(selectedCollection), ids);
      setAddedIds((prev) => new Set([...prev, ...ids]));
      setSelectedIds(new Set());
    } catch (err) {
      setError(err.message);
    } finally {
      setBulkAdding(false);
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

  const clearFilters = () => {
    setFilterDataset('');
    setFilterTaskType('');
  };

  const hasFilters = filterDataset || filterTaskType;

  // Bulk select helpers
  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(results.map((r) => r.id)));
  };

  const deselectAll = () => {
    setSelectedIds(new Set());
  };

  // Results that are selected and not yet added
  const pendingSelectedCount = Array.from(selectedIds).filter(
    (id) => !addedIds.has(id)
  ).length;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Search Examples</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-3">
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

      {/* Search mode toggle */}
      <div className="flex items-center gap-1 mb-3">
        <button
          type="button"
          onClick={() => { setSearchMode('keyword'); setMetadata(null); }}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
            searchMode === 'keyword'
              ? 'bg-red-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Keyword
        </button>
        <button
          type="button"
          onClick={() => { setSearchMode('intelligent'); setMetadata(null); }}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
            searchMode === 'intelligent'
              ? 'bg-red-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Intelligent (AI)
        </button>
      </div>

      {/* Filter bar */}
      {searchMode === 'keyword' && (
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <select
            value={filterDataset}
            onChange={(e) => setFilterDataset(e.target.value)}
            className="border border-gray-300 rounded px-2 py-1 text-xs text-gray-700"
          >
            <option value="">All datasets</option>
            {facets.datasets.map((d) => (
              <option key={d.name} value={d.name}>
                {d.name} ({d.count})
              </option>
            ))}
          </select>

          <select
            value={filterTaskType}
            onChange={(e) => setFilterTaskType(e.target.value)}
            className="border border-gray-300 rounded px-2 py-1 text-xs text-gray-700"
          >
            <option value="">All task types</option>
            {facets.task_types.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name} ({t.count})
              </option>
            ))}
          </select>

          {hasFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className="text-xs text-gray-500 hover:text-red-500 underline"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* Intelligent search metadata banner */}
      {metadata && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 mb-4 text-sm">
          <button
            type="button"
            onClick={() => setMetaExpanded((v) => !v)}
            className="flex items-center justify-between w-full text-left"
          >
            <span className="font-medium text-gray-700">AI search insights</span>
            <span className="text-gray-400 text-xs">{metaExpanded ? 'Hide' : 'Show'}</span>
          </button>
          {metaExpanded && (
            <div className="mt-2 space-y-1 text-gray-600">
              {metadata.explanation && (
                <p>
                  <span className="font-medium text-gray-700">AI understood:</span>{' '}
                  {metadata.explanation}
                </p>
              )}
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {metadata.dataset && (
                  <p>
                    <span className="font-medium text-gray-700">Dataset:</span>{' '}
                    <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                      {metadata.dataset}
                    </span>
                  </p>
                )}
                {metadata.subject && (
                  <p>
                    <span className="font-medium text-gray-700">Subject:</span>{' '}
                    <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                      {metadata.subject}
                    </span>
                  </p>
                )}
              </div>
              {metadata.search_query && metadata.search_query !== query && (
                <p>
                  <span className="font-medium text-gray-700">Expanded query:</span>{' '}
                  <span className="italic text-gray-500">{metadata.search_query}</span>
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Collection selector */}
      <div className="flex items-center gap-2 mb-4 text-sm flex-wrap">
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

      {/* Results toolbar: count + bulk select controls */}
      {results.length > 0 && (
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <p className="text-sm text-gray-500">
            Showing {results.length} of {total} results
            {selectedIds.size > 0 && (
              <span className="ml-2 font-medium text-gray-700">
                — {selectedIds.size} selected
              </span>
            )}
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAll}
              className="text-xs text-gray-500 hover:text-gray-800 underline"
            >
              Select All
            </button>
            {selectedIds.size > 0 && (
              <button
                type="button"
                onClick={deselectAll}
                className="text-xs text-gray-500 hover:text-gray-800 underline"
              >
                Deselect All
              </button>
            )}
            {selectedCollection && pendingSelectedCount > 0 && (
              <button
                type="button"
                onClick={handleBulkAdd}
                disabled={bulkAdding}
                className="text-xs bg-red-500 text-white px-3 py-1.5 rounded-md font-medium hover:bg-red-600 disabled:opacity-50 transition-colors"
              >
                {bulkAdding
                  ? 'Adding...'
                  : `Add Selected (${pendingSelectedCount})`}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="space-y-3">
        {results.map((example) => (
          <div key={example.id} className="flex items-start gap-2">
            {/* Checkbox for bulk select */}
            <input
              type="checkbox"
              checked={selectedIds.has(example.id)}
              onChange={() => toggleSelect(example.id)}
              className="mt-3.5 h-4 w-4 rounded border-gray-300 text-red-500 accent-red-500 flex-shrink-0 cursor-pointer"
              aria-label={`Select example ${example.id}`}
            />
            <div className="flex-1 min-w-0">
              <ExampleCard
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
            </div>
          </div>
        ))}
      </div>

      {/* Empty state: searched but no results */}
      {!loading && results.length === 0 && query && (
        <div className="text-center py-16">
          <p className="text-gray-500 font-medium mb-2">No results found for &ldquo;{query}&rdquo;</p>
          <p className="text-sm text-gray-400 mb-4">Try a different query or adjust your filters.</p>
          {hasFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className="text-xs text-red-500 hover:text-red-700 underline"
            >
              Clear filters and try again
            </button>
          )}
        </div>
      )}

      {/* Empty state: nothing searched yet */}
      {!query && (
        <div className="text-center text-gray-400 py-16">
          <p className="text-lg mb-1 text-gray-500">Search evaluation datasets</p>
          <p className="text-sm mb-3">Find examples by topic, subject, or question text.</p>
          <p className="text-xs text-gray-400">
            Try:{' '}
            {[
              'math problems',
              'python sorting',
              'commonsense',
              'photosynthesis',
              'capital cities',
            ].map((suggestion, i, arr) => (
              <span key={suggestion}>
                <button
                  type="button"
                  className="hover:text-red-500 hover:underline transition-colors"
                  onClick={() => setQuery(suggestion)}
                >
                  {suggestion}
                </button>
                {i < arr.length - 1 && <span className="mx-1">·</span>}
              </span>
            ))}
          </p>
        </div>
      )}
    </div>
  );
}
