interface AssistantAnswerProps {
  answer: string;
  error: string;
  isLoading: boolean;
  language: "el" | "en";
}

export function AssistantAnswer({ answer, error, isLoading, language }: AssistantAnswerProps) {
  if (!answer && !error && !isLoading) return null;
  return (
    <section className="rounded-[2rem] border border-moss/10 bg-mint p-5" aria-live="polite">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-moss">{language === "el" ? "Τοπικός βοηθός" : "Local assistant"}</p>
      {answer && <p className="mt-2 whitespace-pre-wrap leading-7">{answer}</p>}
      {isLoading && <span className="mt-3 inline-block h-2 w-16 animate-pulse rounded-full bg-moss/35" />}
      {error && <p className="mt-2 font-semibold text-red-700">{error}</p>}
    </section>
  );
}
