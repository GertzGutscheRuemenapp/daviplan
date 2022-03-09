import { EventEmitter } from "@angular/core";

export interface BasedataSettings {
  defaultPopAreaLevel: number;
}

export interface PlanningProcess {
  id: number,
  name: string,
  owner: number,
  users: number[],
  allowSharedChange: boolean,
  description?: string,
  scenarios?: Scenario[]
}

export interface Scenario {
  id: number,
  name: string,
  planningProcess: number,
  prognosis?: number,
  modevariants: number[],
  demandratesets: number[]
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
  url?: string,
  name: string,
  description: string,
  group?: number | string,
  layerName?: string,
  attribution?: string,
  active?: boolean,
  legendUrl?: string,
  opacity?: number,
  symbol?: Symbol,
  type?: "wms" | "vector-tiles" | "tiles" | "vector",
  labelField?: string,
  showLabel?: boolean,
  featureSelected?: EventEmitter<{ feature: any, selected: boolean }>
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
  maxPopulation?: number;
}

export interface Area {
  id: number,
  properties: {
    tooltip?: string,
    value?: number,
    areaLevel: number,
    attributes: any,
    label: string,
    description?: string
  }
}

export interface AreaPopulationData {
  areaId: number,
  label?: string,
  value: number
}

export interface PopulationData {
  year: number,
  gender: number,
  agegroup: number,
  value: number
}

export interface AgeGroup {
  id?: number,
  fromAge: number,
  toAge: number,
  label?: string
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
  demandSingularUnit: string;
  demandPluralUnit: string;
  capacitySingularUnit: string;
  capacityPluralUnit: string;
  maxCapacity: number;
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
  properties: {
    name: string,
    infrastructure: number,
    attributes: any,
    label?: string,
    capacity?: number
  },
  capacities?: Capacity[]
}

export interface Capacity {
  id: number,
  place: number,
  service: number,
  capacity: number,
  from_year: number,
  scenario: number
}
