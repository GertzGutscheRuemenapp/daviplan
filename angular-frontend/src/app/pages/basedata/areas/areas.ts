export interface MapSymbol {
  id: number;
  symbol?: undefined;
  fillColor: string;
  strokeColor: string;
}

export interface Layer {
  id: number;
  symbol?: MapSymbol;
}

export interface AreaLevel {
  id: number;
  name: string;
  layer?: Layer;
  preset?: boolean;
}

export const mockPresetLevels: AreaLevel[] = [
  {
    id: 1,
    name: 'Bundesländer',
    layer: {
      id: 1,
      symbol: {
        id: 1,
        fillColor: 'black',
        strokeColor: 'black'
      }
    },
    preset: true
  },
  {
    id: 2,
    name: 'Verwaltungsgemeinschaften',
    layer: {
      id: 2,
      symbol: {
        id: 2,
        fillColor: 'red',
        strokeColor: 'red'
      }
    },
    preset: true
  },
  {
    id: 3,
    name: 'Kreise',
    layer: {
      id: 3,
      symbol: {
        id: 3,
        fillColor: 'yellow',
        strokeColor: 'yellow'
      }
    },
    preset: true
  },
  {
    id: 4,
    name: 'Gemeinden',
    layer: {
      id: 4,
      symbol: {
        id: 4,
        fillColor: 'orange',
        strokeColor: 'orange'
      }
    },
    preset: true
  },
];

export const mockAreaLevels: AreaLevel[] = [
  {
    id: 5,
    name: 'benutzerdefiniert mit ganz langem Namen, um Overflow zu erzwingen',
    layer: {
      id: 5,
      symbol: {
        id: 5,
        fillColor: 'green',
        strokeColor: 'green'
      }
    },
  },
  {
    id: 6,
    name: 'benutzerdefiniert 2',
    layer: {
      id: 6,
      symbol: {
        id: 6,
        fillColor: 'brown',
        strokeColor: 'brown'
      }
    },
  },
];
