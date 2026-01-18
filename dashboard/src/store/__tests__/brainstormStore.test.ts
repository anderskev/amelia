import { describe, it, expect, beforeEach } from "vitest";
import { useBrainstormStore } from "../brainstormStore";
import type { BrainstormingSession, BrainstormMessage } from "@/types/api";

describe("useBrainstormStore", () => {
  beforeEach(() => {
    useBrainstormStore.setState({
      sessions: [],
      activeSessionId: null,
      messages: [],
      artifacts: [],
      isStreaming: false,
      drawerOpen: false,
      streamingMessageId: null,
    });
  });

  describe("session management", () => {
    it("sets sessions list", () => {
      const sessions: BrainstormingSession[] = [
        {
          id: "s1",
          profile_id: "p1",
          driver_session_id: null,
          status: "active",
          topic: "Test",
          created_at: "2026-01-18T00:00:00Z",
          updated_at: "2026-01-18T00:00:00Z",
        },
      ];

      useBrainstormStore.getState().setSessions(sessions);

      expect(useBrainstormStore.getState().sessions).toEqual(sessions);
    });

    it("sets active session", () => {
      useBrainstormStore.getState().setActiveSessionId("s1");

      expect(useBrainstormStore.getState().activeSessionId).toBe("s1");
    });

    it("clears active session", () => {
      useBrainstormStore.getState().setActiveSessionId("s1");
      useBrainstormStore.getState().setActiveSessionId(null);

      expect(useBrainstormStore.getState().activeSessionId).toBeNull();
    });
  });

  describe("message management", () => {
    it("adds a user message", () => {
      const message: BrainstormMessage = {
        id: "m1",
        session_id: "s1",
        sequence: 1,
        role: "user",
        content: "Hello",
        parts: null,
        created_at: "2026-01-18T00:00:00Z",
      };

      useBrainstormStore.getState().addMessage(message);

      expect(useBrainstormStore.getState().messages).toHaveLength(1);
      expect(useBrainstormStore.getState().messages[0]).toEqual(message);
    });

    it("updates existing message content", () => {
      const message: BrainstormMessage = {
        id: "m1",
        session_id: "s1",
        sequence: 1,
        role: "assistant",
        content: "Hello",
        parts: null,
        created_at: "2026-01-18T00:00:00Z",
      };
      useBrainstormStore.getState().addMessage(message);

      useBrainstormStore.getState().updateMessageContent("m1", "Hello world");

      expect(useBrainstormStore.getState().messages[0]!.content).toBe(
        "Hello world"
      );
    });

    it("appends to existing message content", () => {
      const message: BrainstormMessage = {
        id: "m1",
        session_id: "s1",
        sequence: 1,
        role: "assistant",
        content: "Hello",
        parts: null,
        created_at: "2026-01-18T00:00:00Z",
      };
      useBrainstormStore.getState().addMessage(message);

      useBrainstormStore.getState().appendMessageContent("m1", " world");

      expect(useBrainstormStore.getState().messages[0]!.content).toBe(
        "Hello world"
      );
    });

    it("clears messages", () => {
      useBrainstormStore.getState().addMessage({
        id: "m1",
        session_id: "s1",
        sequence: 1,
        role: "user",
        content: "Hello",
        parts: null,
        created_at: "2026-01-18T00:00:00Z",
      });

      useBrainstormStore.getState().clearMessages();

      expect(useBrainstormStore.getState().messages).toHaveLength(0);
    });
  });

  describe("streaming state", () => {
    it("sets streaming state", () => {
      useBrainstormStore.getState().setStreaming(true, "m1");

      expect(useBrainstormStore.getState().isStreaming).toBe(true);
      expect(useBrainstormStore.getState().streamingMessageId).toBe("m1");
    });

    it("clears streaming state", () => {
      useBrainstormStore.getState().setStreaming(true, "m1");
      useBrainstormStore.getState().setStreaming(false, null);

      expect(useBrainstormStore.getState().isStreaming).toBe(false);
      expect(useBrainstormStore.getState().streamingMessageId).toBeNull();
    });
  });

  describe("drawer state", () => {
    it("toggles drawer", () => {
      expect(useBrainstormStore.getState().drawerOpen).toBe(false);

      useBrainstormStore.getState().setDrawerOpen(true);
      expect(useBrainstormStore.getState().drawerOpen).toBe(true);

      useBrainstormStore.getState().setDrawerOpen(false);
      expect(useBrainstormStore.getState().drawerOpen).toBe(false);
    });
  });
});
