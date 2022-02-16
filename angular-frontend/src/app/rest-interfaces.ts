export interface BasedataSettings {
  defaultPopAreaLevel: number;
}

export interface LayerGroup {
  id?: number | string,
  order: number,
  name: string,
  children?: Layer[],
  external?: boolean
}

export interface Symbol {
  fillColor: string,
  strokeColor: string,
  symbol: 'line' | 'circle' | 'square' | 'star'
}

export interface Layer {
  id?: number | string,
  order: number,
  url: string,
  name: string,
  description: string,
  group?: number | string,
  layerName?: string,
  attribution?: string,
  active?: boolean,
  legendUrl?: string,
  opacity?: number,
  symbol?: Symbol,
  type?: "wms" | "vector-tiles" | "tiles",
  labelField?: string
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
  labelField: string;
  tileUrl?: string;
  source?: Source;
  symbol?: Symbol;
  isPreset?: boolean;
  isActive?: boolean;
  areaCount?: number;
}

export interface Area {
  id: number;
  properties: {
    areaLevel: number,
    attributes: any,
    label: string
  }
}

export interface Gender {
  id: number,
  name: string;
}

export interface Service {
  id: number,
  infrastructure: number,
  description: string,
  name: string;
}

export interface Infrastructure {
  id: number,
  name: string;
  description: string;
  services: Service[];
  order: number;
  symbol?: Symbol;
}

export interface Place {
  id: number,
  name: string
}
