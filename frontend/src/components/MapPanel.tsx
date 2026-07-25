import { useEffect, useRef, useState } from "react";
import type { Feature, Polygon } from "geojson";
import maplibregl, { GeoJSONSource, Map as MapLibreMap, Marker } from "maplibre-gl";
import { TerraDraw, TerraDrawPolygonMode, TerraDrawSelectMode } from "terra-draw";
import { TerraDrawMapLibreGLAdapter } from "terra-draw-maplibre-gl-adapter";
import type { Shop } from "../types";

interface MapPanelProps {
  area: Polygon | null;
  shops: Shop[];
  selectedShopId: number | null;
  focusLocation: [number, number] | null;
  language: "el" | "en";
  onAreaChange: (area: Polygon | null) => void;
  onSelectShop: (shopId: number) => void;
}

const rasterStyle = {
  version: 8 as const,
  sources: {
    osm: {
      type: "raster" as const,
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
};

function getCompletePolygon(features: Feature[]): Polygon | null {
  for (const feature of [...features].reverse()) {
    if (feature.geometry.type !== "Polygon") continue;
    if (feature.properties?.currentlyDrawing) continue;

    const polygon = feature.geometry;
    const ring = polygon.coordinates[0];
    if (!ring || ring.length < 4) continue;

    const first = ring[0];
    const last = ring[ring.length - 1];
    const isClosed = first[0] === last[0] && first[1] === last[1];
    const uniqueVertices = new Set(
      ring.slice(0, -1).map(([longitude, latitude]) => `${longitude}:${latitude}`),
    );

    if (isClosed && uniqueVertices.size >= 3) return polygon;
  }

  return null;
}

export function MapPanel({
  area, shops, selectedShopId, focusLocation, language, onAreaChange, onSelectShop,
}: MapPanelProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const drawRef = useRef<TerraDraw | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const initialAreaRef = useRef(area);
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: rasterStyle,
      center: [23.7275, 37.9838],
      zoom: 11,
      attributionControl: {},
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(new maplibregl.GeolocateControl({ trackUserLocation: false }), "top-right");
    map.on("load", () => {
      map.addSource("search-area", {
        type: "geojson",
        data: { type: "Feature", properties: {}, geometry: initialAreaRef.current ?? { type: "Polygon", coordinates: [] } },
      });
      map.addLayer({ id: "search-area-fill", type: "fill", source: "search-area", paint: { "fill-color": "#245c3a", "fill-opacity": 0.14 } });
      map.addLayer({ id: "search-area-line", type: "line", source: "search-area", paint: { "line-color": "#245c3a", "line-width": 3 } });
      const draw = new TerraDraw({
        adapter: new TerraDrawMapLibreGLAdapter({ map }),
        modes: [new TerraDrawPolygonMode(), new TerraDrawSelectMode()],
      });
      draw.start();
      draw.setMode("select");
      draw.on("change", () => {
        onAreaChange(getCompletePolygon(draw.getSnapshot() as Feature[]));
      });
      draw.on("finish", () => {
        onAreaChange(getCompletePolygon(draw.getSnapshot() as Feature[]));
        draw.setMode("select");
        setIsDrawing(false);
      });
      drawRef.current = draw;
    });
    mapRef.current = map;
    return () => {
      drawRef.current?.stop();
      markersRef.current.forEach((marker) => marker.remove());
      map.remove();
      drawRef.current = null;
      mapRef.current = null;
    };
  }, [onAreaChange]);

  useEffect(() => {
    const source = mapRef.current?.getSource("search-area") as GeoJSONSource | undefined;
    if (!source) return;
    const feature: Feature<Polygon> = {
      type: "Feature",
      properties: {},
      geometry: area ?? { type: "Polygon", coordinates: [] },
    };
    source.setData(feature);
  }, [area]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = shops.map((shop) => {
      const element = document.createElement("button");
      element.className = "shop-marker";
      element.type = "button";
      element.textContent = shop.reference;
      element.dataset.active = String(shop.id === selectedShopId);
      element.setAttribute("aria-label", `${shop.reference}: ${language === "el" ? shop.name_el : shop.name_en}`);
      element.addEventListener("click", () => onSelectShop(shop.id));
      return new maplibregl.Marker({ element }).setLngLat([shop.longitude, shop.latitude]).addTo(map);
    });
  }, [language, onSelectShop, selectedShopId, shops]);

  useEffect(() => {
    if (focusLocation && mapRef.current) mapRef.current.flyTo({ center: focusLocation, zoom: 13 });
  }, [focusLocation]);

  function startDrawing() {
    drawRef.current?.clear();
    onAreaChange(null);
    drawRef.current?.setMode("polygon");
    setIsDrawing(true);
  }

  function clearArea() {
    drawRef.current?.clear();
    drawRef.current?.setMode("select");
    setIsDrawing(false);
    onAreaChange(null);
  }

  return (
    <section className="relative min-h-[420px] overflow-hidden rounded-[2rem] bg-mint shadow-panel lg:min-h-0" aria-label={language === "el" ? "Χάρτης αναζήτησης" : "Search map"}>
      <div ref={containerRef} className="absolute inset-0" />
      <div className="absolute left-4 top-4 z-10 flex gap-2">
        <button type="button" onClick={startDrawing} aria-pressed={isDrawing} className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white shadow-lg">
          {isDrawing ? (language === "el" ? "Σχεδιάζεις…" : "Drawing…") : (language === "el" ? "Σχεδίαση περιοχής" : "Draw area")}
        </button>
        <button type="button" onClick={clearArea} className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-ink shadow-lg">
          {language === "el" ? "Καθαρισμός" : "Clear"}
        </button>
      </div>
      {isDrawing && (
        <p className="absolute bottom-7 left-1/2 z-10 -translate-x-1/2 rounded-full bg-white/95 px-4 py-2 text-center text-xs font-bold text-ink shadow-lg">
          {language === "el" ? "Κάνε κλικ σε 3+ σημεία και μετά στο πρώτο σημείο ή πάτησε Enter." : "Click 3+ points, then click the first point or press Enter."}
        </p>
      )}
    </section>
  );
}
