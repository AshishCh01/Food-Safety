import { useCallback, useEffect, useState } from 'react';
import AssistantChat from '../../components/agent/AssistantChat';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import { useAuth } from '../../hooks/useAuth';
import { createAssistantConversation, getAssistantConversation, sendAssistantMessage } from '../../services/agentService';

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
      try {
        await sendAssistantMessage(conversation.id, question, getAccessToken());
        const refreshed = await getAssistantConversation(conversation.id, getAccessToken());
        setConversation(refreshed);
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
