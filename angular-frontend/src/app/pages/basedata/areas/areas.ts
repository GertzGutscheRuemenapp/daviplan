export interface Layer {
  id: number;
}

export interface AreaLevel {
  id: number;
  name: string;
  layer?: Layer;
}

export const mockAreaLevels: AreaLevel[] = [
  {
    id: 1,
    name: 'Bundesland',
    layer: undefined
  },
  {
    id: 2,
    name: 'Gemeinde',
    layer: undefined
  },
];
