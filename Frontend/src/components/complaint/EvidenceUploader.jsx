import { useState } from 'react';

function EvidenceUploader({ evidence, onUpload, readOnly = false }) {
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
    <div className="evidence-uploader">
      {!readOnly && (
        <label className="evidence-upload-label">
          {isUploading ? 'Uploading...' : 'Add photo, video, or PDF evidence'}
          <input type="file" multiple onChange={handleFileChange} disabled={isUploading} />
        </label>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {evidence && evidence.length > 0 ? (
        <ul className="evidence-list">
          {evidence.map((item) => (
            <li key={item.id} className="evidence-list-item">
              {item.download_url ? (
                <a href={item.download_url} target="_blank" rel="noreferrer">
                  {item.file_name}
                </a>
              ) : (
                <span>{item.file_name}</span>
              )}
              <span className="evidence-meta">
                {item.file_type} &middot; {Math.round(item.file_size / 1024)} KB
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p>No evidence uploaded yet.</p>
      )}
    </div>
  );
}

export default EvidenceUploader;
