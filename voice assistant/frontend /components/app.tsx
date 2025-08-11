"use client";

import { useEffect, useMemo, useState } from "react";
import { Room, RoomEvent } from "livekit-client";
import { motion } from "motion/react";
import {
  RoomAudioRenderer,
  RoomContext,
  StartAudio,
} from "@livekit/components-react";
import { toastAlert } from "./alert-toast";
import { SessionView } from "./session-view";
import { Toaster } from "./ui/sonner";
import { Welcome } from "./welcome";
import useConnectionDetails from "@/hooks/useConnectionDetails";
import type { AppConfig } from "@/lib/types";

const MotionWelcome = motion.create(Welcome);
const MotionSessionView = motion.create(SessionView);

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const room = useMemo(() => new Room(), []);
  const [sessionStarted, setSessionStarted] = useState(false);
  const { connectionDetails, refreshConnectionDetails } =
    useConnectionDetails();

  useEffect(() => {
    const onDisconnected = () => {
      setSessionStarted(false);
      refreshConnectionDetails();
    };
    const onMediaDevicesError = (error: Error) => {
      toastAlert({
        title: "Encountered an error with your media devices",
        description: `${error.name}: ${error.message}`,
      });
    };
    room.on(RoomEvent.MediaDevicesError, onMediaDevicesError);
    room.on(RoomEvent.Disconnected, onDisconnected);
    return () => {
      room.off(RoomEvent.Disconnected, onDisconnected);
      room.off(RoomEvent.MediaDevicesError, onMediaDevicesError);
    };
  }, [room, refreshConnectionDetails]);

  useEffect(() => {
    let aborted = false;
    if (sessionStarted && room.state === "disconnected" && connectionDetails) {
      Promise.all([
        room.localParticipant.setMicrophoneEnabled(true, undefined, {
          preConnectBuffer: appConfig.isPreConnectBufferEnabled,
        }),
        room.localParticipant.setCameraEnabled(true),
        room.connect(
          connectionDetails.serverUrl,
          connectionDetails.participantToken,
        ),
      ]).catch((error) => {
        if (aborted) {
          return;
        }
        toastAlert({
          title: "There was an error connecting to the agent",
          description: `${error.name}: ${error.message}`,
        });
      });
    }
    return () => {
      aborted = true;
      room.disconnect();
    };
  }, [
    room,
    sessionStarted,
    connectionDetails,
    appConfig.isPreConnectBufferEnabled,
  ]);

  const { startButtonText } = appConfig;

  return (
    <>
      {!sessionStarted && (
        <MotionWelcome
          key="welcome"
          startButtonText={startButtonText}
          onStartCall={() => setSessionStarted(true)}
          disabled={sessionStarted}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5, ease: "linear" }}
        />
      )}

      {sessionStarted && (
        <RoomContext.Provider value={room}>
          <RoomAudioRenderer />
          <StartAudio label="Start Audio" />
          <MotionSessionView
            key="session-view"
            appConfig={appConfig}
            disabled={!sessionStarted}
            sessionStarted={sessionStarted}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, ease: "linear" }}
          />
        </RoomContext.Provider>
      )}

      <Toaster />
    </>
  );
}
