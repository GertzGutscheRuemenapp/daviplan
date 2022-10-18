import { Geometry } from "ol/geom";

export const DemandTypes = {
  1: ['Nachfragequote', '(z.B. 30% der Kinder einer Altersklasse)'],
  2: ['Nutzungshäufigkeit pro Einwohner und Jahr', '(z.B. 15 Arztbesuche pro Einwohner und Jahr.)'],
  3: ['Einwohnerzahl insgesamt', '(z.B. Brandschutz oder Einzelhandelsversorgung, keine weitere Angaben erforderlich)']
}

export interface BasedataSettings {
  popAreaLevel: number;
  popStatisticsAreaLevel: number;
  defaultModeVariants: { mode: number, variant: number }[];
  defaultDemandRateSets: { service: number, demandrateset: number }[];
  defaultPrognosis: number;
  routing?: {
    baseNet: boolean,
    projectAreaNet: boolean,
    running?: Record<string, boolean>
  };
  processes?: Record<string, boolean>
}

export type Profile = {
  adminAccess: boolean;
  canCreateProcess: boolean;
  canEditBasedata: boolean;
}

export type InfrastructureAccess = {
  infrastructure: number,
  allowSensitiveData: boolean
}

export interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  isSuperuser: boolean;
  password: string;
  profile: Profile;
  access: InfrastructureAccess[];
}

export interface PlanningProcess {
  id: number,
  name: string,
  owner: number,
  users: number[],
  allowSharedChange: boolean,
  description?: string,
  scenarios?: Scenario[],
  infrastructures: number[]
}

export interface Scenario {
  id: number,
  isBase?: boolean,
  name: string,
  planningProcess: number,
  prognosis?: number,
  modeVariants: { mode: number, variant: number }[],
  demandrateSets: { service: number, demandrateset: number }[]
}

export interface Symbol {
  fillColor?: string,
  strokeColor?: string,
  symbol?: 'line' | 'circle' | 'square' | 'star'
}

export interface ExtLayerGroup {
  id?: number,
  order: number,
  name: string,
  external: boolean
}

export interface ExtLayer {
  id: number,
  order: number,
  url: string,
  name: string,
  description: string,
  group: number | string,
  layerName: string,
  active: boolean
}

export interface Source {
  id: number,
  sourceType: 'WFS' | 'FILE',
  layer: string,
  date: string,
  url: string
}

interface IndicatorParameter {
  name: string,
  type : 'choice' | 'number' | 'string',
  title: string,
  choices?: string[];
}

export interface Indicator {
  service: number,
  name: string,
  title: string,
  unit?: string,
  description: string,
  resultType: 'place' | 'area' | 'raster' | 'pop',
  additionalParameters?: IndicatorParameter[]
}

export interface IndicatorLegendClass {
  color: string,
  minValue?: number,
  maxValue?: number
}

export interface RasterCell {
  id: number,
  geom: any,
  cellcode: string,
  population: number,
  value?: number
}

export interface AreaLevel {
  id: number;
  name: string;
  order: number;
  labelField: string;
  keyField: string;
  tileUrl?: string;
  source?: Source;
  symbol?: Symbol;
  isPreset?: boolean;
  isActive?: boolean;
  areaCount?: number;
  isStatisticLevel?: boolean;
  isDefaultPopLevel?: boolean;
  isPopLevel?: boolean;
  areaFields: string[];
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

export interface Year {
  id: number,
  year: number,
  isPrognosis: boolean,
  isReal: boolean,
  hasRealData: boolean,
  hasPrognosisData: boolean
}

export interface Prognosis {
  id: number,
  name: string,
  description: string,
  isDefault: boolean,
  years: number[]
}

export interface AreaIndicatorResult {
  areaId: number,
  label?: string,
  value: number
}

export interface RasterIndicatorResult {
  cellCode: string,
  label?: string,
  value: number
}

export interface PlaceIndicatorResult {
  placeId: number,
  label?: string,
  value: number
}

export interface Population {
  id: number,
  year: number,
  prognosis: number
}

export interface PopEntry {
  id: number,
  population: number,
  area: number,
  gender: number,
  ageGroup: number,
  value: number
}

export interface PopulationData {
  year: number,
  gender: number,
  agegroup: number,
  value: number
}

export interface Statistic {
  id: number,
  year: number
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
  maxCapacity: number,
  demandType: 1 | 2 | 3
}

export interface DemandRate {
  year: number,
  ageGroup: number,
  gender: number,
  value?: number
}

export interface DemandRateSet {
  id: number,
  name: string,
  isDefault: boolean,
  service: number,
  description: string
  demandRates: DemandRate[]
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

export interface PlaceField {
  id?: number,
  fieldType: number
  name: string,
  unit: string,
  sensitive: boolean
}

export interface Infrastructure {
  id: number,
  name: string,
  description: string,
  services: Service[],
  order: number,
  symbol?: Symbol,
  placeFields?: PlaceField[],
  placesCount: number
}

export interface Place {
  id: number,
  geom: string | Geometry,
  name: string,
  infrastructure: number,
  attributes: any,
  label?: string,
  capacity?: number,
  scenario?: number,
  value?: number,
  capacities?: Capacity[]
}

export interface TransitStop {
  id: number,
  geom: string | Geometry,
  name: string
}

export interface TransitMatrixEntry {
  fromStop: number,
  toStop: number,
  minutes: number
}

export interface Capacity {
  id: number,
  place: number,
  service: number,
  capacity: number,
  fromYear: number,
  scenario?: number
}

export enum TransportMode {
  WALK = 1,
  BIKE = 2,
  CAR = 3,
  TRANSIT = 4
}

export interface CellResult {
  cellCode: string,
  value: number
}

export interface PlaceResult {
  placeId: number,
  value: number
}

export interface Network {
  id: number,
  name: string,
  isDefault: boolean
}

export interface ModeVariant {
  id: number,
  label: string,
  mode: number,
  network: number,
  isDefault: boolean
  // cutoffTime: number
}

export interface LogEntry {
  user?: number,
  level: 'ERROR' | 'INFO' | 'DEBUG',
  timestamp: string,
  message: string,
  status?: {success?: boolean}
}
