import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";

import { Thread } from "@/components/assistant-ui/thread";

const adapter: ChatModelAdapter = {
  async *run({ messages }) {
    console.log("messages:", messages);
    const lastMessage = messages[messages.length - 1];

    const message = lastMessage?.content
      .filter((part) => part.type === "text")
      .map((part) => part.text)
      .join("");

    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    yield {
      content: [
        {
          type: "text",
          text: data.answer,
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