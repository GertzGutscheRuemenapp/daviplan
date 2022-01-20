import { AreaLevel } from "../../../rest-interfaces";

export const mockPresetLevels: AreaLevel[] = [
  {
    id: 4,
    name: 'Gemeinden',
    order: 1,
    symbol: {
      symbol: 'line',
      fillColor: 'orange',
      strokeColor: 'orange'
    },
    preset: true
  },
  {
    id: 2,
    name: 'Verwaltungsgemeinschaften',
    order: 1,
    symbol: {
      symbol: 'line',
      fillColor: 'red',
      strokeColor: 'red'
    },
    preset: true
  },
  {
    id: 3,
    name: 'Kreise und kreisfreie Städte',
    order: 1,
    symbol: {
      symbol: 'line',
      fillColor: 'yellow',
      strokeColor: 'yellow'
    },
    preset: true
  },
  {
    id: 1,
    name: 'Bundesländer',
    order: 1,
    symbol: {
      symbol: 'line',
      fillColor: 'black',
      strokeColor: 'black'
    },
    preset: true
  },
];

export const mockAreaLevels: AreaLevel[] = [
  {
    id: 5,
    name: 'benutzerdefiniert mit ganz langem Namen, um Overflow zu erzwingen',
    order: 1,
    symbol: {
      symbol: 'line',
      fillColor: 'green',
      strokeColor: 'green'
    },
  },
  {
    id: 6,
    name: 'benutzerdefiniert 2',
    order: 1,
    symbol: {
      symbol: 'line',
      fillColor: 'brown',
      strokeColor: 'brown'
    },
  },
];
