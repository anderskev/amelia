/**
 * @fileoverview Modal for editing prompt content.
 *
 * Provides a large textarea for editing prompt content, character count
 * with warnings, change note input, and save/reset actions.
 */
import { useState, useEffect, useCallback } from 'react';
import { RotateCcw, AlertTriangle, Save, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { api } from '@/api/client';
import { success, error as showError } from '@/components/Toast';
import type { DefaultContent } from '@/types';

/** Character count threshold for warning. */
const CHAR_WARNING_THRESHOLD = 10000;

interface PromptEditModalProps {
  /** The prompt ID being edited. */
  promptId: string | null;
  /** The prompt name for display. */
  promptName: string;
  /** Whether the modal is open. */
  open: boolean;
  /** Callback to close the modal. */
  onOpenChange: (open: boolean) => void;
  /** Callback when a new version is saved. */
  onSave: () => void;
}

/**
 * Modal for editing prompt content.
 *
 * Features:
 * - Loads default content when opened
 * - Large textarea for editing
 * - Character count with warning for long prompts
 * - Change note input
 * - Reset to default button
 * - Save button that creates a new version
 *
 * @param props - Component props.
 * @returns The prompt edit modal component.
 *
 * @example
 * ```tsx
 * <PromptEditModal
 *   promptId="architect.system"
 *   promptName="Architect System Prompt"
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   onSave={() => revalidate()}
 * />
 * ```
 */
export function PromptEditModal({
  promptId,
  promptName,
  open,
  onOpenChange,
  onSave,
}: PromptEditModalProps) {
  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [changeNote, setChangeNote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [defaultData, setDefaultData] = useState<DefaultContent | null>(null);

  // Load prompt content when modal opens
  useEffect(() => {
    if (!open || !promptId) {
      return;
    }

    const loadContent = async () => {
      setIsLoading(true);
      try {
        // Get default content
        const defaultContent = await api.getPromptDefault(promptId);
        setDefaultData(defaultContent);

        // Get current version if exists
        const prompt = await api.getPrompt(promptId);
        if (prompt.current_version_id && prompt.versions.length > 0) {
          // Find current version and get its content
          const currentVersion = prompt.versions.find(
            (v) => v.id === prompt.current_version_id
          );
          if (currentVersion) {
            // We need to fetch the full version to get content
            // For now, use the API to create version which requires content
            // Actually the versions endpoint returns VersionSummary without content
            // We need to load the default and let user edit from there
            // TODO: Add endpoint to get version content
            setContent(defaultContent.content);
            setOriginalContent(defaultContent.content);
          } else {
            setContent(defaultContent.content);
            setOriginalContent(defaultContent.content);
          }
        } else {
          setContent(defaultContent.content);
          setOriginalContent(defaultContent.content);
        }
      } catch (err) {
        showError('Failed to load prompt content');
        console.error('Failed to load prompt:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadContent();
  }, [open, promptId]);

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      setContent('');
      setOriginalContent('');
      setChangeNote('');
      setDefaultData(null);
    }
  }, [open]);

  const handleResetToDefault = useCallback(() => {
    if (defaultData) {
      setContent(defaultData.content);
    }
  }, [defaultData]);

  const handleSave = useCallback(async () => {
    if (!promptId || !content.trim()) {
      return;
    }

    setIsSaving(true);
    try {
      await api.createPromptVersion(promptId, content, changeNote || null);
      success('Prompt saved successfully');
      onSave();
      onOpenChange(false);
    } catch (err) {
      showError('Failed to save prompt');
      console.error('Failed to save prompt:', err);
    } finally {
      setIsSaving(false);
    }
  }, [promptId, content, changeNote, onSave, onOpenChange]);

  const hasChanges = content !== originalContent;
  const charCount = content.length;
  const isOverThreshold = charCount > CHAR_WARNING_THRESHOLD;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{promptName}</DialogTitle>
          <DialogDescription>
            Edit the prompt content below. Changes will create a new version.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex flex-col gap-4 overflow-hidden">
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Textarea */}
              <div className="flex-1 flex flex-col min-h-0">
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className={cn(
                    'flex-1 w-full min-h-0 resize-none rounded-md border bg-transparent px-3 py-2 text-sm font-mono',
                    'placeholder:text-muted-foreground',
                    'focus-visible:outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]',
                    'disabled:cursor-not-allowed disabled:opacity-50',
                    'dark:bg-input/30 border-input'
                  )}
                  placeholder="Enter prompt content..."
                />
              </div>

              {/* Character count */}
              <div className="flex items-center gap-2 text-sm">
                {isOverThreshold && (
                  <AlertTriangle className="size-4 text-amber-500" />
                )}
                <span
                  className={cn(
                    'text-muted-foreground',
                    isOverThreshold && 'text-amber-500 font-medium'
                  )}
                >
                  {charCount.toLocaleString()} characters
                  {isOverThreshold && (
                    <span className="ml-1">
                      (exceeds {CHAR_WARNING_THRESHOLD.toLocaleString()})
                    </span>
                  )}
                </span>
              </div>

              {/* Change note */}
              <div className="space-y-1.5">
                <label
                  htmlFor="change-note"
                  className="text-sm font-medium text-muted-foreground"
                >
                  Change note (optional)
                </label>
                <Input
                  id="change-note"
                  value={changeNote}
                  onChange={(e) => setChangeNote(e.target.value)}
                  placeholder="Describe what changed..."
                />
              </div>
            </>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="ghost"
            onClick={handleResetToDefault}
            disabled={isLoading || isSaving || !defaultData}
          >
            <RotateCcw className="size-4 mr-2" />
            Reset to default
          </Button>
          <div className="flex-1" />
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isLoading || isSaving || !hasChanges || !content.trim()}
          >
            {isSaving ? (
              <Loader2 className="size-4 mr-2 animate-spin" />
            ) : (
              <Save className="size-4 mr-2" />
            )}
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
