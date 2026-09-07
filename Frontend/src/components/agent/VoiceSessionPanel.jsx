import { useCallback, useEffect, useRef, useState } from 'react';
import { Room, RoomEvent, Track } from 'livekit-client';
import { Mic, MicOff, PhoneCall, PhoneOff } from 'lucide-react';
import Alert from '../ui/Alert';
import Button from '../ui/Button';
import { startLiveKitSession } from '../../services/agentService';

// Voice channel for one Inspector Assistant conversation (see
// docs/AI_AGENTS_ARCHITECTURE.md section 7). Joins a LiveKit room scoped to
// `conversationId`; the LiveKit worker (a separate process, not this app)
// is dispatched into that same room and speaks the assistant's answers -
// this component only handles the WebRTC connection, mic publishing, and
// playing back the agent's audio track. It never calls /voice/turn itself.
function VoiceSessionPanel({ conversationId, token }) {
  const [status, setStatus] = useState('idle'); // idle | connecting | connected | error
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState(null);
  const roomRef = useRef(null);
  const audioContainerRef = useRef(null);

  const disconnect = useCallback(() => {
    roomRef.current?.disconnect();
    roomRef.current = null;
    setStatus('idle');
    setIsMuted(false);
  }, []);

  useEffect(() => disconnect, [disconnect]); // leave the room if the page unmounts mid-call

  async function handleStart() {
    setError(null);
    setStatus('connecting');
    try {
      const session = await startLiveKitSession(conversationId, token);
      const room = new Room();
      roomRef.current = room;

      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === Track.Kind.Audio) {
          const element = track.attach();
          audioContainerRef.current?.appendChild(element);
        }
      });
      room.on(RoomEvent.Disconnected, () => {
        roomRef.current = null;
        setStatus('idle');
      });

      await room.connect(session.livekit_url, session.access_token);
      await room.localParticipant.setMicrophoneEnabled(true);
      setStatus('connected');
    } catch (err) {
      setError(err.message);
      setStatus('error');
      roomRef.current?.disconnect();
      roomRef.current = null;
    }
  }

  async function handleToggleMute() {
    const room = roomRef.current;
    if (!room) return;
    const next = !isMuted;
    await room.localParticipant.setMicrophoneEnabled(!next);
    setIsMuted(next);
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-800">Voice session</p>
          <p className="text-xs text-slate-500">
            {status === 'connected' ? 'Connected — speak your question.' : 'Talk to the assistant instead of typing.'}
          </p>
        </div>

        {status !== 'connected' ? (
          <Button onClick={handleStart} loading={status === 'connecting'} disabled={status === 'connecting'}>
            <PhoneCall className="size-4" aria-hidden="true" />
            Start voice session
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={handleToggleMute}>
              {isMuted ? <MicOff className="size-4" aria-hidden="true" /> : <Mic className="size-4" aria-hidden="true" />}
              {isMuted ? 'Unmute' : 'Mute'}
            </Button>
            <Button variant="danger" onClick={disconnect}>
              <PhoneOff className="size-4" aria-hidden="true" />
              End
            </Button>
          </div>
        )}
      </div>

      {error && <Alert tone="danger">{error}</Alert>}

      {/* Agent audio tracks are attached here as hidden <audio> elements - not
          visually rendered, just needed in the DOM for playback. */}
      <div ref={audioContainerRef} className="hidden" />
    </div>
  );
}

export default VoiceSessionPanel;