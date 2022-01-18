export interface BasedataSettings {
  defaultPopAreaLevel: number;
}

export interface LayerGroup {
  id: number,
  order: number,
  name: string,
  external: boolean,
  children?: Layer[]
}

export interface Symbol {
  fillColor: string,
  strokeColor: string,
  symbol: string
}

export interface Layer {
  id: number,
  group: number,
  order: number,
  url: string,
  name: string,
  layerName: string,
  description: string,
  active?: boolean,
  checked?: boolean,
  legendUrl?: string,
  opacity?: number,
  symbol?: Symbol
}

export interface AreaLevel {
  id: number;
  name: string;
  layer?: Layer;
  preset?: boolean;
}
