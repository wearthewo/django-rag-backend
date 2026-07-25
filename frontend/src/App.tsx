import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import type { Polygon } from "geojson";
import { AssistantAnswer } from "./components/AssistantAnswer";
import { ResultsList } from "./components/ResultsList";
import { SearchPanel } from "./components/SearchPanel";
import { useRecommendation } from "./hooks/useRecommendation";
import type { Settlement } from "./types";

const MapPanel = lazy(() => import("./components/MapPanel").then((module) => ({ default: module.MapPanel })));

function initialValue(key: string, fallback: string) {
  return new URLSearchParams(window.location.search).get(key) ?? fallback;
}

export function App() {
  const [language, setLanguage] = useState<"el" | "en">(() => initialValue("lang", "el") === "en" ? "en" : "el");
  const [question, setQuestion] = useState("");
  const [area, setArea] = useState<Polygon | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [openNow, setOpenNow] = useState(false);
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null);
  const [focusLocation, setFocusLocation] = useState<[number, number] | null>(null);
  const { shops, answer, error, isLoading, search } = useRecommendation();

  useEffect(() => {
    const params = new URLSearchParams();
    params.set("lang", language);
    window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);
    document.documentElement.lang = language;
  }, [language]);

  const handleAreaChange = useCallback((nextArea: Polygon | null) => setArea(nextArea), []);
  const handleSelectShop = useCallback((shopId: number) => setSelectedShopId(shopId), []);

  function selectLocation(settlement: Settlement) {
    setFocusLocation([settlement.longitude, settlement.latitude]);
  }

  function submit() {
    if (!area) return;
    const typedQuestion = question.trim();
    const hasFilters = categories.length > 0 || openNow;
    if (typedQuestion.length < 2 && !hasFilters) return;
    const filterQuestion = language === "el"
      ? `Βρες καταστήματα: ${categories.join(", ") || "ανοιχτά τώρα"}`
      : `Find shops: ${categories.join(", ") || "open now"}`;
    void search({
      question: typedQuestion.length >= 2 ? typedQuestion : filterQuestion,
      language,
      area,
      filters: { categories, open_now: openNow },
    });
  }

  return (
    <main className="min-h-screen bg-sand p-3 sm:p-5 lg:h-screen lg:overflow-hidden">
      <div className="mx-auto grid h-full max-w-[1600px] gap-4 lg:grid-cols-[380px_minmax(0,1fr)]">
        <div className="lg:overflow-y-auto lg:pr-1">
          <SearchPanel
            language={language} question={question} selectedCategories={categories}
            openNow={openNow} hasArea={Boolean(area)} isLoading={isLoading}
            onLanguageChange={setLanguage} onQuestionChange={setQuestion}
            onCategoriesChange={setCategories} onOpenNowChange={setOpenNow}
            onLocationSelect={selectLocation} onSubmit={submit}
          />
        </div>
        <div className="grid min-h-0 gap-4 lg:grid-rows-[minmax(420px,1fr)_auto]">
          <Suspense fallback={<div className="min-h-[420px] animate-pulse rounded-[2rem] bg-mint" />}>
            <MapPanel area={area} shops={shops} selectedShopId={selectedShopId} focusLocation={focusLocation} language={language} onAreaChange={handleAreaChange} onSelectShop={handleSelectShop} />
          </Suspense>
          <div className="grid max-h-[42vh] gap-4 overflow-y-auto rounded-[2rem] bg-white/55 p-4 lg:grid-cols-[minmax(260px,0.8fr)_minmax(420px,1.2fr)]">
            <AssistantAnswer answer={answer} error={error} isLoading={isLoading} language={language} />
            <ResultsList shops={shops} selectedShopId={selectedShopId} language={language} onSelectShop={handleSelectShop} />
          </div>
        </div>
      </div>
    </main>
  );
}
