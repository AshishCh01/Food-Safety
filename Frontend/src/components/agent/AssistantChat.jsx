import { useState } from 'react';
import { BookOpen, Database } from 'lucide-react';
import { formatDateTime } from '../../utils/formatters';
import Alert from '../ui/Alert';
import Button from '../ui/Button';
import EmptyState from '../ui/EmptyState';
import Spinner from '../ui/Spinner';
import Textarea from '../ui/Textarea';

// Renders one Inspector Assistant conversation: message history plus an
// input box. Clearly separates the assistant's answer text from its RAG
// source citations, the authorized application data it used, and any
// uncertainty banner - everything here is advisory only, never a final
// regulatory or legal finding. See docs/AI_AGENTS_ARCHITECTURE.md section 7.
function AssistantChat({ messages, onSend, isSending, error, isLoading }) {
  const [question, setQuestion] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isSending) return;
    onSend(trimmed);
    setQuestion('');
  }

  return (
    <div className="flex flex-col gap-3">
      {isLoading && <Spinner label="Loading conversation…" />}

      {!isLoading && (
        <div className="flex max-h-112 flex-col gap-3 overflow-y-auto">
          {messages.length === 0 && (
            <EmptyState title="Ask the Inspector Assistant about regulations, inspection procedures, or this case. Answers are advisory only and always show their sources." />
          )}
          {messages.map((message) => (
            <AssistantMessageBubble key={message.id} message={message} />
          ))}
        </div>
      )}

      {error && <Alert tone="danger">{error}</Alert>}

      <form className="flex items-start gap-2" onSubmit={handleSubmit}>
        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question…"
          disabled={isSending || isLoading}
          rows={2}
          className="flex-1"
        />
        <Button type="submit" disabled={isSending || isLoading || !question.trim()} loading={isSending}>
          {isSending ? 'Asking…' : 'Ask'}
        </Button>
      </form>
    </div>
  );
}

function AssistantMessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div
      className={
        isUser
          ? 'ml-auto max-w-[85%] rounded-lg bg-slate-100 px-3 py-2'
          : 'mr-auto max-w-[85%] rounded-lg border border-brand-200 bg-brand-50/50 px-3 py-2'
      }
    >
      <p className="mb-0.5 text-xs font-semibold text-slate-500">{isUser ? 'You' : 'Assistant'}</p>
      <p className="whitespace-pre-wrap text-sm text-slate-800">{message.content}</p>

      {!isUser && message.error_code && (
        <Alert tone="danger" className="mt-2">
          The assistant could not complete this request: {message.error_message || 'Unknown error.'}
        </Alert>
      )}

      {!isUser && !message.error_code && message.is_uncertain && (
        <Alert tone="warning" className="mt-2">
          {message.uncertainty_reason ||
            'The assistant is uncertain about this answer - please verify independently before relying on it.'}
        </Alert>
      )}

      {!isUser && message.citations && message.citations.length > 0 && (
        <div className="mt-2 border-t border-brand-200 pt-2">
          <h4 className="mb-1 flex items-center gap-1 text-xs font-semibold text-slate-600">
            <BookOpen className="size-3.5" aria-hidden="true" />
            Sources
          </h4>
          <ul className="space-y-0.5 pl-1 text-xs text-slate-600">
            {message.citations.map((citation, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <li key={index}>
                {citation.title}
                {citation.source_organization ? ` (${citation.source_organization})` : ''}
                {citation.page_number ? `, page ${citation.page_number}` : ''}
                {citation.section_title ? `, section "${citation.section_title}"` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!isUser && message.application_data_used && message.application_data_used.length > 0 && (
        <div className="mt-2 border-t border-brand-200 pt-2">
          <h4 className="mb-1 flex items-center gap-1 text-xs font-semibold text-slate-600">
            <Database className="size-3.5" aria-hidden="true" />
            Application data used
          </h4>
          <ul className="space-y-0.5 pl-1 text-xs text-slate-600">
            {message.application_data_used.map((entry, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <li key={index}>{entry.label}</li>
            ))}
          </ul>
        </div>
      )}

      {message.created_at && <p className="mt-1.5 text-[11px] text-slate-400">{formatDateTime(message.created_at)}</p>}
    </div>
  );
}

export default AssistantChat;
