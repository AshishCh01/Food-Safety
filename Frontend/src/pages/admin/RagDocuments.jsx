import { useEffect, useState } from 'react';
import { Upload } from 'lucide-react';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Alert from '../../components/ui/Alert';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Pagination from '../../components/ui/Pagination';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import Table from '../../components/ui/Table';
import { useAuth } from '../../hooks/useAuth';
import { formatDate } from '../../utils/formatters';
import { RAG_DOCUMENT_STATUSES, RAG_DOCUMENT_TYPES, configFor } from '../../utils/statusConfig';
import {
  deactivateRagDocument,
  ingestRagDocument,
  listRagDocuments,
  uploadRagDocument,
} from '../../services/ragDocumentService';

const PAGE_SIZE = 20;

const INITIAL_FORM = {
  title: '',
  documentType: 'regulation',
  sourceOrganization: '',
  version: '',
  effectiveDate: '',
  sourceUrl: '',
  businessType: '',
  jurisdiction: 'India',
};

function RagDocuments() {
  const { getAccessToken } = useAuth();
  const [result, setResult] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  const [form, setForm] = useState(INITIAL_FORM);
  const [file, setFile] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [busyDocumentId, setBusyDocumentId] = useState(null);

  function load() {
    listRagDocuments(getAccessToken(), { status: statusFilter || undefined, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [getAccessToken, statusFilter, page]);

  function updateField(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }));
  }

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) return;
    setUploadError(null);
    setIsUploading(true);
    try {
      await uploadRagDocument(form, file, getAccessToken());
      setForm(INITIAL_FORM);
      setFile(null);
      event.target.reset();
      load();
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleIngest(documentId) {
    setBusyDocumentId(documentId);
    try {
      await ingestRagDocument(documentId, getAccessToken());
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyDocumentId(null);
    }
  }

  async function handleDeactivate(documentId) {
    setBusyDocumentId(documentId);
    try {
      await deactivateRagDocument(documentId, getAccessToken());
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyDocumentId(null);
    }
  }

  return (
    <ContentContainer>
      <PageHeader
        title="Knowledge Base"
        description="Official source documents indexed for the Inspector Assistant and Investigation Agent."
      />

      <Card>
        <Card.Header>
          <Card.Title>Upload a document</Card.Title>
        </Card.Header>
        <form onSubmit={handleUpload} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Title" htmlFor="doc-title" required className="sm:col-span-2">
            <Input id="doc-title" value={form.title} onChange={updateField('title')} required />
          </FormField>
          <FormField label="Document type" htmlFor="doc-type" required>
            <Select id="doc-type" value={form.documentType} onChange={updateField('documentType')} required>
              {RAG_DOCUMENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Source organization" htmlFor="doc-source-org" hint="Optional">
            <Input id="doc-source-org" value={form.sourceOrganization} onChange={updateField('sourceOrganization')} />
          </FormField>
          <FormField label="Version" htmlFor="doc-version" hint="Optional">
            <Input id="doc-version" value={form.version} onChange={updateField('version')} />
          </FormField>
          <FormField label="Effective date" htmlFor="doc-effective-date" hint="Optional">
            <Input id="doc-effective-date" type="date" value={form.effectiveDate} onChange={updateField('effectiveDate')} />
          </FormField>
          <FormField label="Business type" htmlFor="doc-business-type" hint="Optional">
            <Input id="doc-business-type" value={form.businessType} onChange={updateField('businessType')} />
          </FormField>
          <FormField label="Jurisdiction" htmlFor="doc-jurisdiction">
            <Input id="doc-jurisdiction" value={form.jurisdiction} onChange={updateField('jurisdiction')} />
          </FormField>
          <FormField label="File" htmlFor="doc-file" required className="sm:col-span-2">
            <input
              id="doc-file"
              type="file"
              accept=".pdf,.txt,.md,.docx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
              required
              className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border file:border-slate-300 file:bg-white file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-50"
            />
          </FormField>
          {uploadError && (
            <Alert tone="danger" className="sm:col-span-2">
              {uploadError}
            </Alert>
          )}
          <Button type="submit" loading={isUploading} className="self-start sm:col-span-2">
            <Upload className="size-4" aria-hidden="true" />
            {isUploading ? 'Uploading…' : 'Upload document'}
          </Button>
        </form>
      </Card>

      <FormField label="Status" htmlFor="doc-status-filter" className="max-w-xs">
        <Select
          id="doc-status-filter"
          value={statusFilter}
          onChange={(event) => {
            setStatusFilter(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All</option>
          {RAG_DOCUMENT_STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </Select>
      </FormField>

      {error && <ErrorState message={error} />}

      {!result && !error && <Skeleton.List rows={4} />}

      {result && result.items.length === 0 && <EmptyState title="No documents uploaded yet." />}

      {result && result.items.length > 0 && (
        <Table>
          <Table.Head>
            <tr>
              <Table.Th>Title</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Chunks</Table.Th>
              <Table.Th>Uploaded</Table.Th>
              <Table.Th>Actions</Table.Th>
            </tr>
          </Table.Head>
          <Table.Body>
            {result.items.map((doc) => {
              const status = configFor(RAG_DOCUMENT_STATUSES, doc.status);
              const busy = busyDocumentId === doc.id;
              return (
                <Table.Tr key={doc.id}>
                  <Table.Td className="font-medium text-slate-900">{doc.title}</Table.Td>
                  <Table.Td>{configFor(RAG_DOCUMENT_TYPES, doc.document_type).label}</Table.Td>
                  <Table.Td>
                    <Badge tone={status.tone}>{status.label}</Badge>
                  </Table.Td>
                  <Table.Td>{doc.chunk_count}</Table.Td>
                  <Table.Td>{formatDate(doc.created_at)}</Table.Td>
                  <Table.Td>
                    <div className="flex gap-2">
                      <Button variant="secondary" size="sm" loading={busy} onClick={() => handleIngest(doc.id)}>
                        {doc.status === 'ingested' ? 'Re-ingest' : 'Ingest'}
                      </Button>
                      {doc.is_active && (
                        <Button variant="ghost" size="sm" loading={busy} onClick={() => handleDeactivate(doc.id)}>
                          Deactivate
                        </Button>
                      )}
                    </div>
                  </Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Body>
        </Table>
      )}

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}
    </ContentContainer>
  );
}

export default RagDocuments;
