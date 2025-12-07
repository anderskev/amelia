import { Loader2 } from 'lucide-react';

export default function HistoryPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
      <h2 className="text-3xl font-display text-primary">Past Runs</h2>
      <p className="text-muted-foreground font-heading text-lg tracking-wide">
        Coming soon
      </p>
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

// Loader function will be added in Plan 09
// export async function loader() { ... }
