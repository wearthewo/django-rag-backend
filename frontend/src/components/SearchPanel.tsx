import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCategories, getLocations } from "../api";
import type { Settlement } from "../types";

interface SearchPanelProps {
  language: "el" | "en";
  question: string;
  selectedCategories: string[];
  openNow: boolean;
  hasArea: boolean;
  isLoading: boolean;
  onLanguageChange: (language: "el" | "en") => void;
  onQuestionChange: (question: string) => void;
  onCategoriesChange: (categories: string[]) => void;
  onOpenNowChange: (openNow: boolean) => void;
  onLocationSelect: (settlement: Settlement) => void;
  onSubmit: () => void;
}

export function SearchPanel({
  language, question, selectedCategories, openNow, hasArea, isLoading,
  onLanguageChange, onQuestionChange, onCategoriesChange, onOpenNowChange,
  onLocationSelect, onSubmit,
}: SearchPanelProps) {
  const [locationQuery, setLocationQuery] = useState("");
  const [showLocations, setShowLocations] = useState(false);
  const categories = useQuery({
    queryKey: ["categories"],
    queryFn: ({ signal }) => getCategories(signal),
    retry: false,
    staleTime: Infinity,
  });
  const locations = useQuery({
    queryKey: ["locations", locationQuery],
    queryFn: ({ signal }) => getLocations(locationQuery, signal),
    enabled: locationQuery.trim().length >= 2,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  function toggleCategory(category: string) {
    onCategoriesChange(selectedCategories.includes(category)
      ? selectedCategories.filter((item) => item !== category)
      : [...selectedCategories, category]);
  }

  function selectLocation(settlement: Settlement) {
    setLocationQuery(language === "el" ? settlement.name_el || settlement.name : settlement.name_en || settlement.name);
    setShowLocations(false);
    onLocationSelect(settlement);
  }

  const hasSearchIntent = question.trim().length >= 2 || selectedCategories.length > 0 || openNow;

  return (
    <aside className="rounded-[2rem] bg-white p-5 shadow-panel lg:p-7">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-coral">Agora Scout</p>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-ink">{language === "el" ? "Βρες το σωστό μέρος" : "Find the right place"}</h1>
        </div>
        <button type="button" onClick={() => onLanguageChange(language === "el" ? "en" : "el")} className="rounded-full border border-ink/15 px-3 py-2 text-sm font-bold" aria-label="Change language">
          {language === "el" ? "EN" : "ΕΛ"}
        </button>
      </div>

      <label className="block text-sm font-bold" htmlFor="location">{language === "el" ? "Πήγαινε σε περιοχή" : "Go to a place"}</label>
      <div className="relative mt-2">
        <input
          id="location"
          value={locationQuery}
          onChange={(event) => {
            setLocationQuery(event.target.value);
            setShowLocations(true);
          }}
          onFocus={() => setShowLocations(locationQuery.trim().length >= 2)}
          onBlur={(event) => {
            if (!event.currentTarget.parentElement?.contains(event.relatedTarget)) setShowLocations(false);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") setShowLocations(false);
          }}
          placeholder={language === "el" ? "π.χ. Αθήνα" : "e.g. Athens"}
          className="w-full rounded-2xl border border-ink/15 bg-sand px-4 py-3 outline-none focus:border-moss focus:ring-2 focus:ring-mint"
          autoComplete="off"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showLocations && Boolean(locations.data?.length)}
          aria-controls="location-options"
        />
        {showLocations && locations.data && locations.data.length > 0 && (
          <ul id="location-options" role="listbox" className="absolute z-20 mt-2 max-h-48 w-full overflow-auto rounded-2xl border border-ink/10 bg-white p-2 shadow-panel">
            {locations.data.map((settlement) => (
              <li key={settlement.id} role="option" aria-selected="false">
                <button type="button" onClick={() => selectLocation(settlement)} className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-mint">
                  {language === "el" ? settlement.name_el || settlement.name : settlement.name_en || settlement.name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <fieldset className="mt-6">
        <legend className="text-sm font-bold">{language === "el" ? "Τι ψάχνεις;" : "What are you looking for?"}</legend>
        <div className="mt-3 flex flex-wrap gap-2">
          {categories.data?.map((category) => {
            const active = selectedCategories.includes(category.key);
            return (
              <button key={category.key} type="button" aria-pressed={active} onClick={() => toggleCategory(category.key)} className={`rounded-full border px-3 py-2 text-sm font-semibold transition ${active ? "border-moss bg-moss text-white" : "border-ink/10 bg-sand hover:border-moss"}`}>
                {language === "el" ? category.el : category.en}
              </button>
            );
          })}
        </div>
        {categories.isError && (
          <div className="mt-3 flex items-center justify-between gap-3 rounded-xl bg-coral/10 px-3 py-2 text-xs text-ink">
            <span>{language === "el" ? "Δεν φορτώθηκαν οι κατηγορίες." : "Categories could not be loaded."}</span>
            <button type="button" onClick={() => void categories.refetch()} className="font-bold underline">
              {language === "el" ? "Ξανά" : "Retry"}
            </button>
          </div>
        )}
      </fieldset>

      <label className="mt-6 flex cursor-pointer items-center gap-3 text-sm font-semibold">
        <input type="checkbox" checked={openNow} onChange={(event) => onOpenNowChange(event.target.checked)} className="h-5 w-5 accent-moss" />
        {language === "el" ? "Ανοιχτά 24/7" : "Open 24/7"}
      </label>

      <label className="mt-6 block text-sm font-bold" htmlFor="question">{language === "el" ? "Ρώτησε τον τοπικό βοηθό" : "Ask the local assistant"}</label>
      <textarea id="question" value={question} onChange={(event) => onQuestionChange(event.target.value)} rows={4} maxLength={500} placeholder={language === "el" ? "Θέλω ένα ήσυχο καφέ κοντά στο κέντρο…" : "I want a quiet café near the centre…"} className="mt-2 w-full resize-none rounded-2xl border border-ink/15 bg-sand px-4 py-3 outline-none focus:border-moss focus:ring-2 focus:ring-mint" />
      <button type="button" onClick={onSubmit} disabled={!hasArea || !hasSearchIntent || isLoading} className="mt-4 w-full rounded-2xl bg-coral px-5 py-3.5 font-black text-white shadow-lg transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-45">
        {isLoading ? (language === "el" ? "Αναζήτηση…" : "Searching…") : (language === "el" ? "Βρες επιλογές" : "Find options")}
      </button>
      {!hasArea && <p className="mt-2 text-center text-xs text-ink/60">{language === "el" ? "Σχεδίασε πρώτα μια περιοχή στον χάρτη." : "Draw an area on the map first."}</p>}
    </aside>
  );
}
