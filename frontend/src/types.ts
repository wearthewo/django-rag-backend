import type { Polygon } from "geojson";

export interface Category { key: string; el: string; en: string; icon: string }
export interface Shop {
  id: number;
  slug: string;
  reference: string;
  name: string;
  name_el: string;
  name_en: string;
  category: string;
  address: string;
  phone: string;
  website: string;
  opening_hours: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  match_reason: string;
}
export interface Settlement {
  id: number;
  name: string;
  name_el: string;
  name_en: string;
  kind: string;
  latitude: number;
  longitude: number;
}
export interface SearchRequest {
  question: string;
  language: "el" | "en";
  area: Polygon;
  filters: { categories: string[]; open_now: boolean; max_distance_km?: number };
}
