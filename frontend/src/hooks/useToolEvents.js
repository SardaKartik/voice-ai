import { useEffect, useState } from "react";
import { RoomEvent } from "livekit-client";

const decoder = new TextDecoder("utf-8");

/**
 * Subscribes to LiveKit room data packets and collects tool_call events for UI feeds.
 *
 * @param {import("livekit-client").Room | null | undefined} room
 * @returns {{ toolEvents: object[], summary: object | null }}
 */
export function useToolEvents(room) {
  const [toolEvents, setToolEvents] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!room) {
      return undefined;
    }

    setToolEvents([]);
    setSummary(null);

    /**
     * @param {Uint8Array} payload
     */
    function onDataReceived(payload) {
      let text;
      try {
        text = decoder.decode(payload);
        const event = JSON.parse(text);

        if (event.type !== "tool_call") {
          return;
        }

        const withTimestamp = {
          ...event,
          timestamp: new Date().toLocaleTimeString(),
        };

        setToolEvents((prev) => [...prev, withTimestamp]);

        if (event.tool === "end_conversation") {
          setSummary(withTimestamp);
        }
      } catch {
        // Ignore invalid UTF-8 or non-JSON payloads
      }
    }

    room.on(RoomEvent.DataReceived, onDataReceived);

    return () => {
      room.off(RoomEvent.DataReceived, onDataReceived);
    };
  }, [room]);

  return { toolEvents, summary };
}
