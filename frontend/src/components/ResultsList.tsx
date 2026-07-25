import type { Shop } from "../types";

interface ResultsListProps {
  shops: Shop[];
  selectedShopId: number | null;
  language: "el" | "en";
  onSelectShop: (shopId: number) => void;
}

export function ResultsList({ shops, selectedShopId, language, onSelectShop }: ResultsListProps) {
  if (!shops.length) return null;
  return (
    <section aria-label={language === "el" ? "Αποτελέσματα" : "Results"}>
      <div className="mb-3 flex items-end justify-between">
        <h2 className="text-xl font-black">{language === "el" ? "Καλύτερες επιλογές" : "Best matches"}</h2>
        <span className="text-sm text-ink/55">{shops.length}</span>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {shops.map((shop) => {
          const selected = shop.id === selectedShopId;
          const name = language === "el" ? shop.name_el || shop.name : shop.name_en || shop.name;
          return (
            <article key={shop.id} className={`rounded-2xl border p-4 transition ${selected ? "border-coral bg-white shadow-lg" : "border-ink/10 bg-white/75"}`}>
              <button type="button" onClick={() => onSelectShop(shop.id)} className="w-full text-left">
                <div className="flex items-start justify-between gap-3">
                  <div><span className="text-xs font-black text-coral">{shop.reference}</span><h3 className="text-lg font-black">{name}</h3></div>
                  <span className="whitespace-nowrap rounded-full bg-sand px-2 py-1 text-xs font-bold">{shop.distance_km} km</span>
                </div>
                <p className="mt-2 text-sm text-ink/65">{shop.match_reason}</p>
                {shop.address && <p className="mt-2 text-sm">{shop.address}</p>}
                {shop.opening_hours && <p className="mt-1 text-xs font-semibold text-moss">{shop.opening_hours}</p>}
              </button>
              <a href={`https://www.openstreetmap.org/?mlat=${shop.latitude}&mlon=${shop.longitude}#map=18/${shop.latitude}/${shop.longitude}`} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm font-bold text-moss underline decoration-moss/30 underline-offset-4">{language === "el" ? "Άνοιγμα στον χάρτη" : "Open on map"}</a>
            </article>
          );
        })}
      </div>
    </section>
  );
}
