import { useState } from 'react';

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
    <div className="assistant-chat">
      {isLoading && <p>Loading conversation...</p>}

      {!isLoading && (
        <div className="assistant-messages">
          {messages.length === 0 && (
            <p className="assistant-empty">
              Ask the Inspector Assistant about regulations, inspection procedures, or this case. Answers are
              advisory only and always show their sources.
            </p>
          )}
          {messages.map((message) => (
            <AssistantMessageBubble key={message.id} message={message} />
          ))}
        </div>
      )}

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <form className="assistant-input-form" onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question..."
          disabled={isSending || isLoading}
          rows={2}
        />
        <button type="submit" disabled={isSending || isLoading || !question.trim()}>
          {isSending ? 'Asking...' : 'Ask'}
        </button>
      </form>
    </div>
  );
}

function AssistantMessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`assistant-message assistant-message-${message.role}`}>
      <p className="assistant-message-speaker">{isUser ? 'You' : 'Assistant'}</p>
      <p className="assistant-message-content">{message.content}</p>

      {!isUser && message.error_code && (
        <p className="form-error" role="alert">
          The assistant could not complete this request: {message.error_message || 'Unknown error.'}
        </p>
      )}

      {!isUser && !message.error_code && message.is_uncertain && (
        <p className="assistant-uncertain-banner" role="alert">
          {message.uncertainty_reason ||
            'The assistant is uncertain about this answer - please verify independently before relying on it.'}
        </p>
      )}

      {!isUser && message.citations && message.citations.length > 0 && (
        <div className="assistant-citations">
          <h4>Sources</h4>
          <ul>
            {message.citations.map((citation, index) => (
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
        <div className="assistant-app-data">
          <h4>Application data used</h4>
          <ul>
            {message.application_data_used.map((entry, index) => (
              <li key={index}>{entry.label}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default AssistantChat;
