import { useMemo } from "react";
import {
  type ReceivedChatMessage,
  type TextStreamData,
  useChat,
  useRoomContext,
  useTranscriptions,
} from "@livekit/components-react";

export default function useChatAndTranscription() {
  const transcriptions: TextStreamData[] = useTranscriptions();
  const chat = useChat();
  const room = useRoomContext();

  const mergedTranscriptions = useMemo(() => {
    const merged: Array<ReceivedChatMessage> = [
      ...transcriptions.map((transcription) => ({
        id: transcription.streamInfo.id,
        timestamp: transcription.streamInfo.timestamp,
        message: transcription.text,
        from: undefined,
      })),
      ...chat.chatMessages,
    ];
    return merged.sort((a, b) => a.timestamp - b.timestamp);
  }, [transcriptions, chat.chatMessages, room]);

  return { messages: mergedTranscriptions, send: chat.send };
}
