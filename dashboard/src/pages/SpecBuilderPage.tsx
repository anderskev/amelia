import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, Plus, Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/PageHeader";
import { useBrainstormStore } from "@/store/brainstormStore";
import { useBrainstormSession } from "@/hooks/useBrainstormSession";
import {
  SessionDrawer,
  ArtifactCard,
  HandoffDialog,
} from "@/components/brainstorm";
import type { BrainstormArtifact } from "@/types/api";

export default function SpecBuilderPage() {
  const navigate = useNavigate();
  const {
    activeSessionId,
    messages,
    artifacts,
    isStreaming,
    setDrawerOpen,
  } = useBrainstormStore();

  const {
    loadSessions,
    loadSession,
    createSession,
    sendMessage,
    deleteSession,
    handoff,
    startNewSession,
  } = useBrainstormSession();

  const [inputValue, setInputValue] = useState("");
  const [handoffArtifact, setHandoffArtifact] = useState<BrainstormArtifact | null>(null);
  const [isHandingOff, setIsHandingOff] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleSubmit = useCallback(async () => {
    const content = inputValue.trim();
    if (!content || isSubmitting) return;

    setIsSubmitting(true);
    setInputValue("");

    try {
      if (activeSessionId) {
        await sendMessage(content);
      } else {
        // Create new session with first message
        // TODO: Get actual profile ID from settings
        await createSession("default", content);
      }
    } catch (error) {
      setInputValue(content); // Restore on error
      // TODO: Show error toast
    } finally {
      setIsSubmitting(false);
    }
  }, [inputValue, isSubmitting, activeSessionId, sendMessage, createSession]);

  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      await loadSession(sessionId);
    },
    [loadSession]
  );

  const handleDeleteSession = useCallback(
    async (sessionId: string) => {
      await deleteSession(sessionId);
    },
    [deleteSession]
  );

  const handleHandoffClick = useCallback((artifact: BrainstormArtifact) => {
    setHandoffArtifact(artifact);
  }, []);

  const handleHandoffConfirm = useCallback(
    async (issueTitle: string) => {
      if (!handoffArtifact) return;

      setIsHandingOff(true);
      try {
        const result = await handoff(handoffArtifact.path, issueTitle);
        setHandoffArtifact(null);
        // Navigate to the new workflow
        navigate(`/workflows/${result.workflow_id}`);
      } finally {
        setIsHandingOff(false);
      }
    },
    [handoffArtifact, handoff, navigate]
  );

  const handleHandoffCancel = useCallback(() => {
    setHandoffArtifact(null);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <PageHeader>
        <PageHeader.Left>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open sessions"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <PageHeader.Title>Spec Builder</PageHeader.Title>
        </PageHeader.Left>
        <PageHeader.Right>
          <Button variant="outline" size="sm" onClick={startNewSession}>
            <Plus className="h-4 w-4 mr-2" />
            New Session
          </Button>
        </PageHeader.Right>
      </PageHeader>

      {/* Session Drawer */}
      <SessionDrawer
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onNewSession={startNewSession}
      />

      {/* Conversation Area */}
      <div className="flex-1 overflow-auto px-4 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Lightbulb className="h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-lg font-medium mb-2">Start a brainstorming session</h2>
            <p className="text-muted-foreground max-w-md">
              Type a message below to begin exploring ideas and producing design documents.
            </p>
          </div>
        ) : (
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "p-4 rounded-lg",
                  message.role === "user"
                    ? "ml-auto max-w-[80%] bg-secondary"
                    : "bg-muted"
                )}
              >
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {message.content}
                </div>
              </div>
            ))}

            {/* Inline artifacts */}
            {artifacts.map((artifact) => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                onHandoff={handleHandoffClick}
                isHandingOff={isHandingOff && handoffArtifact?.id === artifact.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t bg-background p-4">
        <div className="max-w-3xl mx-auto">
          <Textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="What would you like to design?"
            disabled={isStreaming}
            className="min-h-[80px] resize-none"
          />
          <div className="flex justify-end mt-2">
            <Button
              onClick={handleSubmit}
              disabled={!inputValue.trim() || isStreaming}
            >
              {isStreaming ? "Thinking..." : "Send"}
            </Button>
          </div>
        </div>
      </div>

      {/* Handoff Dialog */}
      <HandoffDialog
        open={handoffArtifact !== null}
        artifact={handoffArtifact}
        onConfirm={handleHandoffConfirm}
        onCancel={handleHandoffCancel}
        isLoading={isHandingOff}
      />
    </div>
  );
}
