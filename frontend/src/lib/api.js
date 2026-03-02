const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  // 204 No Content
  if (res.status === 204) return null;
  // Check if response is a file download
  const disposition = res.headers.get('content-disposition');
  if (disposition && disposition.includes('attachment')) {
    const blob = await res.blob();
    const filename = disposition.match(/filename="(.+)"/)?.[1] || 'export';
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    return { downloaded: filename };
  }
  return res.json();
}

// Datasets
export const listDatasets = () => request('/datasets');
export const getDataset = (id) => request(`/datasets/${id}`);

// Examples
export const listExamples = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/examples?${qs}`);
};
export const getExample = (id) => request(`/examples/${id}`);

// Search
export const searchKeyword = (query, options = {}) =>
  request('/search', {
    method: 'POST',
    body: JSON.stringify({ query, ...options }),
  });

// Collections
export const listCollections = () => request('/collections');
export const getCollection = (id) => request(`/collections/${id}`);
export const createCollection = (name, description) =>
  request('/collections', {
    method: 'POST',
    body: JSON.stringify({ name, description }),
  });
export const updateCollection = (id, data) =>
  request(`/collections/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
export const deleteCollection = (id) =>
  request(`/collections/${id}`, { method: 'DELETE' });
export const listCollectionExamples = (id) =>
  request(`/collections/${id}/examples`);
export const addExamplesToCollection = (id, exampleIds) =>
  request(`/collections/${id}/examples`, {
    method: 'POST',
    body: JSON.stringify({ example_ids: exampleIds }),
  });
export const removeExampleFromCollection = (collId, exId) =>
  request(`/collections/${collId}/examples/${exId}`, { method: 'DELETE' });

// Export
export const exportCollection = (id, format) =>
  request(`/collections/${id}/export`, {
    method: 'POST',
    body: JSON.stringify({ format }),
  });
