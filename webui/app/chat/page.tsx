import { ChatStream } from "@/components/chat/ChatStream";

export const metadata = { title: "Reasoning · Cosmos3-Nano" };

export default function ChatPage() {
  return (
    <section aria-label="Reasoning chat">
      <h1>Reasoning</h1>
      <ChatStream />
    </section>
  );
}
