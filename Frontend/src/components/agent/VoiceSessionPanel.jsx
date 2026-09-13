import { useCallback, useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Square, Loader2 } from 'lucide-react';
import Alert from '../ui/Alert';
import Button from '../ui/Button';


import { API_BASE_URL } from '../../services/api';

const workletCode = `
class PCMProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input && input.length > 0) {
      const channelData = input[0];
      const pcm16 = new Int16Array(channelData.length);
      for (let i = 0; i < channelData.length; i++) {
        let s = Math.max(-1, Math.min(1, channelData[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
    }
    return true;
  }
}
registerProcessor('pcm-processor', PCMProcessor);
`;

function VoiceSessionPanel({ conversationId, token }) {
  const [status, setStatus] = useState('idle'); // idle | connecting | listening | processing | speaking | error
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState(null);
  const [transcript, setTranscript] = useState('');
  
  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const nextStartTimeRef = useRef(0);
  const activeSourcesRef = useRef([]);

  const isAgentDoneGeneratingRef = useRef(false);

  const cleanup = useCallback(() => {
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'closed' }));
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    isAgentDoneGeneratingRef.current = false;
    nextStartTimeRef.current = 0;
    setIsMuted(false);
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const toggleMute = useCallback(() => {
    if (streamRef.current) {
      const audioTracks = streamRef.current.getAudioTracks();
      if (audioTracks.length > 0) {
        const currentlyMuted = !audioTracks[0].enabled;
        audioTracks[0].enabled = currentlyMuted;
        setIsMuted(!currentlyMuted);
      }
    }
  }, []);

  const scheduleNextAudio = useCallback(() => {
    if (!audioCtxRef.current || audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      if (isAgentDoneGeneratingRef.current) {
        isAgentDoneGeneratingRef.current = false;
        setStatus('listening');
        setTranscript('');
      }
      return;
    }
    
    isPlayingRef.current = true;
    const audioData = audioQueueRef.current.shift();
    
    try {
      const float32Array = new Float32Array(audioData);
      const buffer = audioCtxRef.current.createBuffer(1, float32Array.length, 16000);
      buffer.getChannelData(0).set(float32Array);

      const source = audioCtxRef.current.createBufferSource();
      source.buffer = buffer;
      source.connect(audioCtxRef.current.destination);
      
      let startTime = Math.max(audioCtxRef.current.currentTime, nextStartTimeRef.current);
      source.start(startTime);
      nextStartTimeRef.current = startTime + buffer.duration;
      activeSourcesRef.current.push(source);
      
      source.onended = () => {
        activeSourcesRef.current = activeSourcesRef.current.filter(s => s !== source);
        scheduleNextAudio();
      };
    } catch (err) {
      console.error('Audio processing error', err);
      scheduleNextAudio();
    }
  }, []);

  async function handleStart() {
    cleanup();
    setError(null);
    setTranscript('');
    setStatus('connecting');
    isAgentDoneGeneratingRef.current = false;
    setIsMuted(false);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
      streamRef.current = stream;

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      audioCtxRef.current = audioCtx;

      const blob = new Blob([workletCode], { type: 'application/javascript' });
      const url = URL.createObjectURL(blob);
      await audioCtx.audioWorklet.addModule(url);

      const wsUrl = `${API_BASE_URL.replace(/^http/, 'ws')}/api/v1/voice/ws/${conversationId}?token=${token}`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ type: 'start' }));
      };

      ws.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          const msg = JSON.parse(event.data);
          if (msg.type === 'ready') {
            const source = audioCtx.createMediaStreamSource(stream);
            const processor = new AudioWorkletNode(audioCtx, 'pcm-processor');
            processorRef.current = processor;

            processor.port.onmessage = (e) => {
              if (ws.readyState === WebSocket.OPEN) {
                ws.send(e.data);
              }
            };
            source.connect(processor);
            processor.connect(audioCtx.destination);
            setStatus('listening');
          } else if (msg.type === 'transcript_partial' || msg.type === 'transcript_final') {
            if (msg.text.trim()) {
              audioQueueRef.current = [];
              activeSourcesRef.current.forEach(source => {
                try { source.stop(); } catch (e) {}
              });
              activeSourcesRef.current = [];
              isPlayingRef.current = false;
              isAgentDoneGeneratingRef.current = false;
              setStatus('listening');
              ws.send(JSON.stringify({ type: 'stop_agent' }));
            }
            setTranscript(msg.text);
            if (msg.type === 'transcript_final' && msg.text.trim()) {
                setStatus('processing');
                ws.send(JSON.stringify({ type: 'invoke_agent', text: msg.text }));
            }
          } else if (msg.type === 'assistant_start') {
            setStatus('speaking');
            setTranscript('');
            isAgentDoneGeneratingRef.current = false;
          } else if (msg.type === 'assistant_text') {
            setTranscript(prev => prev + msg.text);
          } else if (msg.type === 'assistant_end') {
            isAgentDoneGeneratingRef.current = true;
            if (!isPlayingRef.current && audioQueueRef.current.length === 0) {
                isAgentDoneGeneratingRef.current = false;
                setStatus('listening');
                setTranscript('');
            }
          } else if (msg.type === 'error') {
            setError(msg.message);
            setStatus('error');
            cleanup();
          }
        } else if (event.data instanceof Blob) {
          const arrayBuffer = await event.data.arrayBuffer();
          audioQueueRef.current.push(arrayBuffer);
          if (!isPlayingRef.current) {
            scheduleNextAudio();
          }
        }
      };

      ws.onerror = () => {
        setError("Voice connection could not be established. Please try again.");
        setStatus('error');
        cleanup();
      };
      
      ws.onclose = () => {
        if (wsRef.current === ws) {
          setStatus('idle');
          cleanup();
        }
      };

    } catch (err) {
      console.error(err);
      setError("Microphone permission denied or unavailable.");
      setStatus('error');
      cleanup();
    }
  }

  function handleStop() {
    setStatus('idle');
    cleanup();
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-brand-200 bg-brand-50/30 p-4 shadow-sm">
      <div className="flex flex-col items-center justify-center gap-4 py-2">
        {status === 'idle' || status === 'error' ? (
          <button
            type="button"
            onClick={handleStart}
            className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-600 text-white shadow-lg transition hover:bg-brand-700 hover:scale-105 active:scale-95"
          >
            <Mic className="size-8" aria-hidden="true" />
          </button>
        ) : (
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={toggleMute}
              className={`flex h-16 w-16 items-center justify-center rounded-full text-white shadow-lg transition hover:scale-105 active:scale-95 ${isMuted ? 'bg-amber-500 hover:bg-amber-600' : 'bg-slate-400 hover:bg-slate-500'}`}
              title={isMuted ? "Unmute" : "Mute"}
            >
              {isMuted ? <MicOff className="size-6" aria-hidden="true" /> : <Mic className="size-6" aria-hidden="true" />}
            </button>
            <button
              type="button"
              onClick={handleStop}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500 text-white shadow-lg transition hover:bg-red-600 hover:scale-105 active:scale-95"
              title="Stop Session"
            >
              <Square className="size-6 fill-current" aria-hidden="true" />
            </button>
          </div>
        )}
        
        <div className="text-center">
          {status === 'idle' && <p className="text-sm font-medium text-slate-600">🎙️ Tap to talk</p>}
          {status === 'connecting' && <p className="text-sm font-medium text-slate-600 flex items-center gap-2"><Loader2 className="animate-spin size-4" /> Connecting...</p>}
          {status === 'listening' && <p className="text-sm font-medium text-red-600">🔴 Listening...</p>}
          {status === 'processing' && <p className="text-sm font-medium text-amber-600">⏳ Thinking...</p>}
          {status === 'speaking' && <p className="text-sm font-medium text-brand-600">🔊 Assistant speaking...</p>}
          {status === 'error' && <p className="text-sm font-medium text-red-600">Voice unavailable</p>}
        </div>
      </div>

      {transcript && (
        <div className="rounded bg-white p-3 text-sm text-slate-700 shadow-inner min-h-[3rem]">
          {transcript}
        </div>
      )}

      {error && <Alert tone="danger" className="mt-2">{error}</Alert>}
    </div>
  );
}

export default VoiceSessionPanel;