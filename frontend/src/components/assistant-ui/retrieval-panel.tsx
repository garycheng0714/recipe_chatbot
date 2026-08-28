import { useState } from "react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export type RetrievalContext = {
  id: string;
  answer: string;
  topic: string;
};

type RetrievalPanelProps = {
  contexts: RetrievalContext[];
};

export function RetrievalPanel({
  contexts,
}: RetrievalPanelProps) {
  const [open, setOpen] = useState(false);

  return (
    <Collapsible
      className="mt-3 w-full"
      open={open}
      onOpenChange={setOpen}
    >
      <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <span>{open ? "▼" : "▶"}</span>

        Retrieved Context ({contexts.length})
      </CollapsibleTrigger>

      <CollapsibleContent className="mt-2 space-y-2">
        {contexts.map((context, index) => (
          <div
            key={context.id}
            className="rounded-lg border bg-muted/30 p-3 text-sm"
          >
            <div className="mb-1 flex items-center justify-between">
              <span className="font-medium">
                Chunk #{index + 1}
              </span>

              <span className="text-xs text-muted-foreground">
                {context.topic}
              </span>
            </div>

            <p className="text-muted-foreground">
              {context.answer}
            </p>
          </div>
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}