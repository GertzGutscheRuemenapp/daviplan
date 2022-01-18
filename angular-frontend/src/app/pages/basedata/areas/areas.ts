import { AreaLevel } from "../../../backendInterfaces";

export const mockPresetLevels: AreaLevel[] = [
  {
    id: 4,
    name: 'Gemeinden',
    layer: {
      id: 4,
      order: 1,
      group: 1,
      url: '',
      layerName: '',
      description: '',
      name: '',
      symbol: {
        symbol: 'line',
        fillColor: 'orange',
        strokeColor: 'orange'
      }
    },
    preset: true
  },
  {
    id: 2,
    name: 'Verwaltungsgemeinschaften',
    layer: {
      id: 2,
      order: 1,
      group: 1,
      url: '',
      layerName: '',
      description: '',
      name: '',
      symbol: {
        symbol: 'line',
        fillColor: 'red',
        strokeColor: 'red'
      }
    },
    preset: true
  },
  {
    id: 3,
    name: 'Kreise und kreisfreie Städte',
    layer: {
      id: 3,
      order: 1,
      group: 1,
      url: '',
      layerName: '',
      description: '',
      name: '',
      symbol: {
        symbol: 'line',
        fillColor: 'yellow',
        strokeColor: 'yellow'
      }
    },
    preset: true
  },
  {
    id: 1,
    name: 'Bundesländer',
    layer: {
      id: 1,
      order: 1,
      group: 1,
      url: '',
      layerName: '',
      description: '',
      name: '',
      symbol: {
        symbol: 'line',
        fillColor: 'black',
        strokeColor: 'black'
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
      order: 1,
      group: 1,
      url: '',
      layerName: '',
      description: '',
      name: '',
      symbol: {
        symbol: 'line',
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
      order: 1,
      group: 1,
      url: '',
      layerName: '',
      description: '',
      name: '',
      symbol: {
        symbol: 'line',
        fillColor: 'brown',
        strokeColor: 'brown'
      }
    },
  },
];
