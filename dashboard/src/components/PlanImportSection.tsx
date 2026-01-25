/**
 * @fileoverview Reusable collapsible section for importing external plans.
 */
import { useState, useCallback, useEffect } from 'react';
import { ChevronDown, FileText, ClipboardPaste, File } from 'lucide-react';
import { cn } from '@/lib/utils';
import { parsePlanPreview, type PlanPreview } from '@/lib/plan-parser';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

/**
 * Plan data passed to parent component.
 */
export interface PlanData {
  /** Path to external plan file (relative to worktree). */
  plan_file?: string;
  /** Inline plan markdown content. */
  plan_content?: string;
}

export interface PlanImportSectionProps {
  /** Callback when plan data changes. */
  onPlanChange: (data: PlanData) => void;
  /** Whether the section is expanded by default. */
  defaultExpanded?: boolean;
  /** Error message to display. */
  error?: string;
  /** Additional CSS classes. */
  className?: string;
}

type InputMode = 'file' | 'paste';

/**
 * Collapsible section for importing external plans via file path or pasted content.
 */
export function PlanImportSection({
  onPlanChange,
  defaultExpanded = false,
  error,
  className,
}: PlanImportSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultExpanded);
  const [mode, setMode] = useState<InputMode>('file');
  const [filePath, setFilePath] = useState('');
  const [content, setContent] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [preview, setPreview] = useState<PlanPreview | null>(null);

  // Update preview when content changes
  useEffect(() => {
    if (mode === 'paste' && content.trim()) {
      const parsed = parsePlanPreview(content);
      // Only show preview if we extracted something meaningful
      if (parsed.goal || parsed.taskCount > 0 || parsed.keyFiles.length > 0) {
        setPreview(parsed);
      } else {
        setPreview(null);
      }
    } else {
      setPreview(null);
    }
  }, [mode, content]);

  // Notify parent of changes
  useEffect(() => {
    if (mode === 'file') {
      onPlanChange({
        plan_file: filePath.trim() || undefined,
        plan_content: undefined,
      });
    } else {
      onPlanChange({
        plan_file: undefined,
        plan_content: content.trim() || undefined,
      });
    }
  }, [mode, filePath, content, onPlanChange]);

  const handleModeChange = useCallback((value: string) => {
    if (value) {
      setMode(value as InputMode);
    }
  }, []);

  const handleFilePathChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setFilePath(e.target.value);
    },
    []
  );

  const handleContentChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setContent(e.target.value);
    },
    []
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    const mdFile = files.find((f) => f.name.endsWith('.md'));

    if (!mdFile) {
      return;
    }

    try {
      const text = await mdFile.text();
      setContent(text);
    } catch {
      // Failed to read file - silently ignore
    }
  }, []);

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className={cn('border border-border rounded-lg', className)}
    >
      <CollapsibleTrigger className="flex items-center justify-between w-full px-4 py-3 hover:bg-muted/50 transition-colors rounded-lg">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">External Plan</span>
        </div>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-muted-foreground transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </CollapsibleTrigger>

      <CollapsibleContent className="px-4 pb-4 space-y-4">
        {/* Mode toggle */}
        <ToggleGroup
          type="single"
          value={mode}
          onValueChange={handleModeChange}
          className="w-full"
        >
          <ToggleGroupItem
            value="file"
            aria-label="File path"
            className="flex-1 gap-2"
          >
            <File className="w-4 h-4" />
            File
          </ToggleGroupItem>
          <ToggleGroupItem
            value="paste"
            aria-label="Paste content"
            className="flex-1 gap-2"
          >
            <ClipboardPaste className="w-4 h-4" />
            Paste
          </ToggleGroupItem>
        </ToggleGroup>

        {/* File path input */}
        {mode === 'file' && (
          <Input
            type="text"
            placeholder="Relative path to plan file (e.g., docs/plan.md)"
            value={filePath}
            onChange={handleFilePathChange}
          />
        )}

        {/* Paste content textarea */}
        {mode === 'paste' && (
          <div
            data-testid="plan-import-drop-zone"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              'rounded-md transition-colors',
              isDragOver && 'border-primary bg-primary/5'
            )}
          >
            <Textarea
              placeholder="Paste your plan markdown here..."
              value={content}
              onChange={handleContentChange}
              rows={8}
              className={cn(
                'min-h-[150px]',
                isDragOver && 'border-primary'
              )}
            />
          </div>
        )}

        {/* Error display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Plan preview */}
        {preview && (
          <div
            data-testid="plan-preview"
            className="border border-border rounded-lg p-3 bg-muted/30 space-y-2"
          >
            {preview.goal && (
              <div>
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Goal
                </span>
                <p className="text-sm mt-0.5 line-clamp-2">{preview.goal}</p>
              </div>
            )}
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              {preview.taskCount > 0 && (
                <span>{preview.taskCount} tasks</span>
              )}
              {preview.keyFiles.length > 0 && (
                <span className="truncate">
                  {preview.keyFiles[0]}
                  {preview.keyFiles.length > 1 &&
                    ` +${preview.keyFiles.length - 1} more`}
                </span>
              )}
            </div>
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}
