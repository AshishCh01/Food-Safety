import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import AssistantChat from './AssistantChat';

const USER_MESSAGE = { id: 'm1', role: 'user', content: 'What are the hand hygiene rules?' };

const ASSISTANT_MESSAGE = {
  id: 'm2',
  role: 'assistant',
  content: 'Wash hands before handling food, per FSSAI guidance.',
  citations: [
    { document_id: 'd1', title: 'FSSAI Hygiene Guidelines', source_organization: 'FSSAI', page_number: 5, section_title: 'Personal Hygiene' },
  ],
  application_data_used: [{ tool: 'A1', label: 'Current complaint', summary: {} }],
  is_uncertain: false,
  uncertainty_reason: null,
  error_code: null,
  error_message: null,
  created_at: '2026-08-27T12:00:00Z',
};

describe('AssistantChat', () => {
  it('shows an empty-state prompt when there are no messages', () => {
    render(<AssistantChat messages={[]} onSend={() => {}} isSending={false} error={null} isLoading={false} />);

    expect(screen.getByText(/ask the inspector assistant/i)).toBeInTheDocument();
  });

  it('shows a loading state instead of messages', () => {
    render(<AssistantChat messages={[]} onSend={() => {}} isSending={false} error={null} isLoading />);

    expect(screen.getByText(/loading conversation/i)).toBeInTheDocument();
    expect(screen.queryByText(/ask the inspector assistant/i)).not.toBeInTheDocument();
  });

  it('calls onSend with the typed question and clears the input', () => {
    const onSend = vi.fn();
    render(<AssistantChat messages={[]} onSend={onSend} isSending={false} error={null} isLoading={false} />);

    const textarea = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(textarea, { target: { value: 'What is the sampling procedure?' } });
    fireEvent.click(screen.getByRole('button', { name: /^ask$/i }));

    expect(onSend).toHaveBeenCalledWith('What is the sampling procedure?');
    expect(textarea.value).toBe('');
  });

  it('does not call onSend for a blank question', () => {
    const onSend = vi.fn();
    render(<AssistantChat messages={[]} onSend={onSend} isSending={false} error={null} isLoading={false} />);

    expect(screen.getByRole('button', { name: /^ask$/i })).toBeDisabled();
  });

  it('disables input and shows a sending state while a question is in flight', () => {
    render(<AssistantChat messages={[]} onSend={() => {}} isSending error={null} isLoading={false} />);

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /asking/i })).toBeDisabled();
  });

  it('renders a user message and an assistant message with citations and application data used', () => {
    render(
      <AssistantChat
        messages={[USER_MESSAGE, ASSISTANT_MESSAGE]}
        onSend={() => {}}
        isSending={false}
        error={null}
        isLoading={false}
      />
    );

    expect(screen.getByText(USER_MESSAGE.content)).toBeInTheDocument();
    expect(screen.getByText(ASSISTANT_MESSAGE.content)).toBeInTheDocument();
    expect(screen.getByText(/fssai hygiene guidelines/i)).toBeInTheDocument();
    expect(screen.getByText(/page 5/i)).toBeInTheDocument();
    expect(screen.getByText('Current complaint')).toBeInTheDocument();
  });

  it('shows an uncertainty banner when the assistant message is flagged uncertain', () => {
    const uncertain = { ...ASSISTANT_MESSAGE, is_uncertain: true, uncertainty_reason: 'No matching documents found.' };
    render(
      <AssistantChat messages={[uncertain]} onSend={() => {}} isSending={false} error={null} isLoading={false} />
    );

    expect(screen.getByRole('alert')).toHaveTextContent(/no matching documents found/i);
  });

  it('shows a failure message for an assistant message with an error_code', () => {
    const failed = { ...ASSISTANT_MESSAGE, error_code: 'GEMINI_UNAVAILABLE', error_message: 'Service unavailable.' };
    render(<AssistantChat messages={[failed]} onSend={() => {}} isSending={false} error={null} isLoading={false} />);

    expect(screen.getByText(/could not complete this request/i)).toBeInTheDocument();
    expect(screen.getByText(/service unavailable/i)).toBeInTheDocument();
  });

  it('shows a request-level error separately from message content', () => {
    render(
      <AssistantChat messages={[]} onSend={() => {}} isSending={false} error="Network error" isLoading={false} />
    );

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });
});
