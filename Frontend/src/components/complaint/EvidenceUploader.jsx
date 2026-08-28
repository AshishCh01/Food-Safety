import { useId, useState } from 'react';
import { FileText, Paperclip, UploadCloud } from 'lucide-react';
import Alert from '../ui/Alert';
import EmptyState from '../ui/EmptyState';
import Spinner from '../ui/Spinner';

function EvidenceUploader({ evidence, onUpload, readOnly = false, renderExtra }) {
  const inputId = useId();
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFileChange(event) {
    const files = Array.from(event.target.files || []);
    event.target.value = '';
    if (files.length === 0) return;

    setError(null);
    setIsUploading(true);
    try {
      for (const file of files) {
        // eslint-disable-next-line no-await-in-loop
        await onUpload(file);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {!readOnly && (
        <label
          htmlFor={inputId}
          className="flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-4 text-sm font-medium text-slate-600 hover:border-brand-400 hover:bg-brand-50/40"
        >
          {isUploading ? (
            <Spinner label="Uploading…" />
          ) : (
            <>
              <UploadCloud className="size-4.5 text-slate-400" aria-hidden="true" />
              Add photo, video, or PDF evidence
            </>
          )}
          <input id={inputId} type="file" multiple onChange={handleFileChange} disabled={isUploading} className="sr-only" />
        </label>
      )}
      {error && <Alert tone="danger">{error}</Alert>}
      {evidence && evidence.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {evidence.map((item) => (
            <li key={item.id} className="rounded-md border border-slate-200 px-3 py-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                {item.download_url ? (
                  <a
                    href={item.download_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex min-w-0 items-center gap-1.5 text-sm font-medium text-brand-700 hover:underline"
                  >
                    <Paperclip className="size-3.5 shrink-0" aria-hidden="true" />
                    <span className="truncate">{item.file_name}</span>
                  </a>
                ) : (
                  <span className="flex items-center gap-1.5 text-sm text-slate-700">
                    <FileText className="size-3.5 shrink-0" aria-hidden="true" />
                    {item.file_name}
                  </span>
                )}
                <span className="shrink-0 text-xs text-slate-500">
                  {item.file_type} &middot; {Math.round(item.file_size / 1024)} KB
                </span>
              </div>
              {renderExtra && renderExtra(item)}
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState title="No evidence uploaded yet." className="py-6" />
      )}
    </div>
  );
}

export default EvidenceUploader;
