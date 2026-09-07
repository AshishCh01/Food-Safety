import { useCallback, useEffect, useState } from 'react';
import AssistantChat from '../../components/agent/AssistantChat';
import VoiceSessionPanel from '../../components/agent/VoiceSessionPanel';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import { useAuth } from '../../hooks/useAuth';
import { createAssistantConversation, getAssistantConversation, sendAssistantMessageStream } from '../../services/agentService';

// General Inspector Assistant entry point (no complaint/inspection context) -
// for regulatory/procedural questions that aren't tied to a specific case.
// Case-scoped follow-up questions are handled inline on InspectionDetails.
function InspectorAssistant() {
  const { getAccessToken } = useAuth();
  const [conversation, setConversation] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const isLoading = !conversation && !error;

  useEffect(() => {
    let cancelled = false;
    createAssistantConversation(getAccessToken())
      .then((data) => {
        if (!cancelled) setConversation(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

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
    [conversation, getAccessToken],
  );

  return (
    <ContentContainer className="max-w-3xl">
      <PageHeader
        title="Inspector Assistant"
        description="Ask about food-safety regulations, inspection guidelines, or procedures. Answers are advisory only and always show their sources - they never replace your own judgement or a formal finding."
      />
      <Card>
        {conversation && <VoiceSessionPanel conversationId={conversation.id} token={getAccessToken()} />}
        <AssistantChat
          messages={conversation ? conversation.messages : []}
          onSend={handleSend}
          isSending={isSending}
          error={error}
          isLoading={isLoading}
        />
      </Card>
    </ContentContainer>
  );
}

export default InspectorAssistant;