function formatKey(key) {
  return key
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatValue(value) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/** Renders an arbitrary flat key/value object (e.g. an audit log's `details`
 * payload) as readable rows instead of a raw JSON dump. */
function DetailsList({ data }) {
  const entries = Object.entries(data || {});
  if (entries.length === 0) return null;

  return (
    <dl className="mt-2 grid grid-cols-1 gap-x-4 gap-y-1 rounded-md bg-slate-50 p-2.5 text-xs sm:grid-cols-[max-content_1fr]">
      {entries.map(([key, value]) => (
        <div key={key} className="contents">
          <dt className="font-medium text-slate-500">{formatKey(key)}</dt>
          <dd className="m-0 break-words text-slate-700">{formatValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export default DetailsList;
