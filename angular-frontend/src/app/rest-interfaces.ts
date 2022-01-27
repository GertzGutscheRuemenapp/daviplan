export interface BasedataSettings {
  defaultPopAreaLevel: number;
}

export interface LayerGroup {
  id: number,
  order: number,
  name: string,
  children?: Layer[],
  external?: boolean
}

export interface Symbol {
  fillColor: string,
  strokeColor: string,
  symbol: string
}

export interface Layer {
  id: number,
  order: number,
  url: string,
  name: string,
  description: string,
  group?: number,
  layerName?: string,
  attribution?: string,
  active?: boolean,
  legendUrl?: string,
  opacity?: number,
  symbol?: Symbol,
  type?: "wms" | "vector-tiles" | "tiles";
}

export interface Source {
  id: number;
  sourceType: string;
  date: string;
  url: string;
}

export interface AreaLevel {
  id: number;
  name: string;
  order: number;
  tileUrl?: string;
  source?: Source;
  symbol?: Symbol;
  isPreset?: boolean;
  isActive?: boolean;
  areaCount?: number;
}
