import { useCallback, useEffect, useState } from 'react';
import { useLocation, matchPath } from 'react-router-dom';
import { Bot, X, Maximize2, Minimize2, CheckSquare } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import AssistantChat from '../agent/AssistantChat';
import VoiceSessionPanel from '../agent/VoiceSessionPanel';
import Card from '../ui/Card';
import Button from '../ui/Button';
import {
  createAssistantConversation,
  getAssistantConversation,
  listAssistantConversations,
  sendAssistantMessageStream,
} from '../../services/agentService';
import { getAssignment } from '../../services/inspectionService';

function GlobalInspectorAssistant() {
  const { getAccessToken, user } = useAuth();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine if we are on an inspection page to grab context
  const match = matchPath({ path: '/inspector/assignments/:assignmentId', end: false }, location.pathname);
  const currentAssignmentId = match?.params?.assignmentId;

  const [inspectionId, setInspectionId] = useState(null);
  const [useCaseContext, setUseCaseContext] = useState(true);
  const [complaintContext, setComplaintContext] = useState(null);

  const [conversation, setConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);

  // Load inspection context if on assignment page
  useEffect(() => {
    let cancelled = false;
    if (currentAssignmentId) {
      getAssignment(currentAssignmentId, getAccessToken())
        .then((data) => {
          if (!cancelled) {
            setInspectionId(data.inspection?.id || null);
            setComplaintContext(data.complaint || null);
          }
        })
        .catch(() => {
          // Ignore failures, just no context
        });
    } else {
      setInspectionId(null);
      setComplaintContext(null);
    }
    return () => {
      cancelled = true;
    };
  }, [currentAssignmentId, getAccessToken]);

  // Load or create conversation when panel opens or when context toggles
  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const activeInspectionId = useCaseContext ? inspectionId : null;
    const token = getAccessToken();

    listAssistantConversations(token, { inspectionId: activeInspectionId })
      .then((result) =>
        result.items.length > 0
          ? getAssistantConversation(result.items[0].id, token)
          : createAssistantConversation(token, { inspectionId: activeInspectionId })
      )
      .then((data) => {
        if (!cancelled) {
          setConversation(data);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isOpen, inspectionId, useCaseContext, getAccessToken]);

  const handleSend = useCallback(
    async (question) => {
      if (!conversation) return;
      setError(null);
      setIsSending(true);

      const userMsg = { id: `temp-user-${Date.now()}`, role: 'user', content: question, created_at: new Date().toISOString() };
      const assistantTempId = `temp-assistant-${Date.now()}`;
      const assistantMsg = {
        id: assistantTempId,
        role: 'assistant',
        content: '',
        isStreaming: true,
        created_at: new Date().toISOString(),
      };

      setConversation((prev) => ({
        ...prev,
        messages: [...(prev?.messages || []), userMsg, assistantMsg],
      }));

      try {
        await sendAssistantMessageStream(conversation.id, question, getAccessToken(), {
          onToken: (tokenDelta) => {
            setConversation((prev) => {
              if (!prev) return prev;
              const updated = prev.messages.map((msg) =>
                msg.id === assistantTempId ? { ...msg, content: msg.content + tokenDelta } : msg
              );
              return { ...prev, messages: updated };
            });
          },
          onDone: (doneData) => {
            setConversation((prev) => {
              if (!prev) return prev;
              const updated = prev.messages.map((msg) =>
                msg.id === assistantTempId
                  ? {
                      ...msg,
                      id: doneData.message_id || msg.id,
                      isStreaming: false,
                      citations: doneData.citations,
                      application_data_used: doneData.application_data_used,
                      is_uncertain: doneData.is_uncertain,
                      uncertainty_reason: doneData.uncertainty_reason,
                    }
                  : msg
              );
              return { ...prev, messages: updated };
            });
          },
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setIsSending(false);
      }
    },
    [conversation, getAccessToken]
  );

  const suggestedQuestions =
    inspectionId && useCaseContext
      ? ['Summarize this complaint', 'What should I inspect?', 'What regulations are relevant?', 'What evidence should I verify?']
      : ['What should I check during a food inspection?', 'What are food storage requirements?', 'Explain hygiene requirements.', 'What regulations apply to food adulteration?'];

  if (user?.role !== 'inspector') return null;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col items-end sm:bottom-6 sm:right-6">
      {/* Chat Panel */}
      {isOpen && (
        <Card
          className={`mb-4 flex flex-col overflow-hidden shadow-2xl transition-all duration-300 ease-in-out ${
            isExpanded ? 'h-[80vh] w-[90vw] sm:w-[600px]' : 'h-[550px] w-[90vw] max-h-[80vh] sm:w-[400px]'
          }`}
          padded={false}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-brand-200 bg-brand-50 px-4 py-3">
            <div className="flex items-center gap-2 text-brand-900">
              <Bot className="size-5" />
              <div className="flex flex-col">
                <h3 className="font-semibold leading-tight">Inspector AI</h3>
                <span className="text-[10px] text-slate-500 font-medium">Food Safety Assistant</span>
              </div>
            </div>
            <div className="flex items-center gap-1 text-slate-500">
              <button
                type="button"
                className="rounded p-1 hover:bg-brand-100"
                onClick={() => setIsExpanded(!isExpanded)}
                aria-label={isExpanded ? 'Minimize' : 'Maximize'}
              >
                {isExpanded ? <Minimize2 className="size-4" /> : <Maximize2 className="size-4" />}
              </button>
              <button
                type="button"
                className="rounded p-1 hover:bg-brand-100"
                onClick={() => setIsOpen(false)}
                aria-label="Close Inspector AI Assistant"
              >
                <X className="size-4" />
              </button>
            </div>
          </div>

          {/* Context Banner */}
          {inspectionId && (
            <div className="flex items-center justify-between border-b border-brand-100 bg-slate-50 px-4 py-2 text-xs">
              <div className="flex items-center gap-2">
                <CheckSquare className="size-4 text-brand-600" />
                <span className="font-medium text-slate-700">
                  Current Case: {complaintContext?.complaint_number || 'Loading...'}
                </span>
              </div>
              <label className="flex items-center gap-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useCaseContext}
                  onChange={(e) => setUseCaseContext(e.target.checked)}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-600 size-3"
                />
                <span className="text-slate-600">Use Case Context</span>
              </label>
            </div>
          )}

          {/* Chat Area */}
          <div className="flex flex-1 flex-col overflow-y-auto p-4 bg-white relative">
            {/* Suggested Questions */}
            {(!conversation || conversation.messages.length === 0) && !isLoading && (
              <div className="mb-6 flex flex-col gap-2">
                <p className="text-sm text-slate-600 font-medium">Suggested Questions</p>
                <div className="flex flex-wrap gap-2">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      className="text-left text-xs bg-slate-50 border border-slate-200 rounded-full px-3 py-1.5 text-slate-700 hover:bg-brand-50 hover:border-brand-200 transition-colors"
                      onClick={() => handleSend(q)}
                      disabled={isSending || isLoading}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {conversation && <VoiceSessionPanel conversationId={conversation.id} token={getAccessToken()} />}
            <AssistantChat
              messages={conversation ? conversation.messages : []}
              onSend={handleSend}
              isSending={isSending}
              error={error}
              isLoading={isLoading}
            />
          </div>
        </Card>
      )}

      {/* Floating Button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="flex h-14 items-center gap-2 rounded-full px-5 shadow-lg transition-transform hover:scale-105 active:scale-95 bg-brand-600 text-white"
          aria-label="Open Inspector AI Assistant"
        >
          <Bot className="size-5" />
          <span className="font-semibold">Ask AI</span>
        </Button>
      )}
    </div>
  );
}

export default GlobalInspectorAssistant;
