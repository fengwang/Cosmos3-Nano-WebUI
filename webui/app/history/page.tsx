import { HistoryList } from "@/components/history/HistoryList";

export const metadata = { title: "History · Cosmos3-Nano" };

export default function HistoryPage() {
  return (
    <section aria-label="Job history">
      <h1>History</h1>
      <HistoryList />
    </section>
  );
}
