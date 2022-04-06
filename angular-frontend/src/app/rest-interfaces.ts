import { EventEmitter } from "@angular/core";
import { Geometry } from "ol/geom";

export interface BasedataSettings {
  defaultPopAreaLevel: number,
  popStatisticsAreaLevel: number,
  defaultDemandRateSets: Record<number, number>,
  defaultModeVariants: Record<number, number>,
  defaultPrognosis: number
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
  modevariants: Record<number, number>,
  demandratesets: Record<number, number>
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
  sourceType: 'WFS' | 'FILE';
  date: string;
  url: string;
}

export interface Indicator {
  id: number;
  service: number;
  name: string;
  description: string;
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
  isStatisticLevel?: boolean;
  isDefaultPopLevel?: boolean;
  maxValues?: {
    population: number,
    immigration?: number,
    emigration?: number,
    births?: number,
    deaths?: number,
    natureDiff: number,
    migrationDiff: number
  }
}

export interface Area {
  id: number,
  geometry: string | Geometry,
  centroid?: Geometry,
  properties: {
    tooltip?: string,
    value?: number,
    areaLevel: number,
    attributes: any,
    label: string,
    description?: string
  }
}

export interface Prognosis {
  id: number,
  name: string,
  isDefault: boolean,
  years: number[]
}

export interface AreaIndicatorData {
  areaId: number,
  label?: string,
  value: number
}

export interface Population {
  id: number,
  year: number,
  prognosis: number
}

export interface PopulationData {
  year: number,
  gender: number,
  agegroup: number,
  value: number
}

export interface StatisticsData {
  id: number,
  popstatistic: number,
  year: number,
  area: number,
  immigration: number,
  emigration: number,
  births: number,
  deaths: number
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
  name: string,
  demandSingularUnit: string,
  demandPluralUnit: string,
  hasCapacity: boolean,
  capacitySingularUnit: string,
  capacityPluralUnit: string,
  facilitySingularUnit: 'der' | 'die' | 'das',
  facilityArticle: string,
  facilityPluralUnit: string,
  directionWayRelationship: 1 | 2,
  minCapacity: number,
  maxCapacity: number
}

export interface FClass {
  order: number,
  value: string
}

export interface FieldType{
  id: number,
  name: string,
  ftype: 'CLA' | 'NUM' | 'STR',
  classification?: FClass[]
}

export interface PlaceField{
  id: number,
  name: string,
  unit: string,
  infrastructure: number,
  fieldType: FieldType,
  sensitive: boolean
}

export interface Infrastructure {
  id: number,
  name: string,
  description: string,
  services: Service[],
  order: number,
  symbol?: Symbol,
  placeFields?: PlaceField[]
}

export interface Place {
  id: number,
  geometry: string | Geometry,
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
