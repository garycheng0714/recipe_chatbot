import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";

import { Thread } from "@/components/assistant-ui/thread";

const adapter: ChatModelAdapter = {
  async *run({ messages }) {
    console.log("messages:", messages);

    yield {
      content: [
        {
          type: "text",
          text: "Hello! Assistant UI is working 🎉",
        },
      ],
    };
  },
};

function App() {
  const runtime = useLocalRuntime(adapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="dark h-screen bg-background text-foreground">
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}

export default App;