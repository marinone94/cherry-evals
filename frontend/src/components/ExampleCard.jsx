export default function ExampleCard({ example, actions }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 mb-1">{example.question}</p>
          {example.answer && (
            <p className="text-sm text-gray-600">
              <span className="font-medium text-green-700">Answer:</span> {example.answer}
            </p>
          )}
          {example.choices && example.choices.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {example.choices.map((c, i) => (
                <span
                  key={i}
                  className={`inline-block px-2 py-0.5 text-xs rounded-full ${
                    c === example.answer
                      ? 'bg-green-100 text-green-800 font-medium'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {c}
                </span>
              ))}
            </div>
          )}
          <div className="mt-2 flex items-center gap-3 text-xs text-gray-400">
            <span>ID: {example.id}</span>
            {example.dataset_name && <span>{example.dataset_name}</span>}
            {example.example_metadata?.subject && (
              <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                {example.example_metadata.subject}
              </span>
            )}
          </div>
        </div>
        {actions && <div className="flex-shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
