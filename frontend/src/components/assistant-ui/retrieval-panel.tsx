import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export type RetrievalContext = {
  content: string;
  score?: number;
};

type RetrievalPanelProps = {
  contexts: RetrievalContext[];
};

export function RetrievalPanel({
  contexts,
}: RetrievalPanelProps) {
  return (
    <Collapsible className="mt-3 w-full">
      <CollapsibleTrigger className="text-sm text-muted-foreground hover:text-foreground">
        ▶ Retrieved Context ({contexts.length})
      </CollapsibleTrigger>

      <CollapsibleContent className="mt-2 space-y-2">
        {contexts.map((context, index) => (
          <div
            key={index}
            className="rounded-lg border bg-muted/40 p-3 text-sm"
          >
            <div className="mb-1 flex justify-between">
              <span className="font-medium">
                Chunk #{index + 1}
              </span>

              {context.score !== undefined && (
                <span className="text-xs text-muted-foreground">
                  {context.score.toFixed(3)}
                </span>
              )}
            </div>

            <p className="text-muted-foreground">
              {context.content}
            </p>
          </div>
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}