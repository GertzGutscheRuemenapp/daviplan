import { WKT } from "ol/format";
import { Geometry } from "ol/geom";

export function arrayMove(array: any[], fromIndex: number, toIndex: number) {
  const element = array[fromIndex];
  array.splice(fromIndex, 1);
  array.splice(toIndex, 0, element);
}

export function sortBy(array: any[], attr: string, options: { reverse: boolean } = { reverse: false }): any[]{
  let sorted = array.sort((a, b) =>
    (a[attr] > b[attr])? 1: (a[attr] < b[attr])? -1: 0);
  if (options.reverse)
    sorted = sorted.reverse();
  return sorted;
}

export function wktToGeom(wkt: string, options?: { targetProjection?: string, dataProjection?: string, ewkt?: boolean }): Geometry {
  const targetProjection = (options?.targetProjection !== undefined)? options?.targetProjection: 'EPSG:4326';
  const format = new WKT()
  let dataProjection = options?.dataProjection || 'EPSG:4326';
  if (options?.ewkt){
    const split = wkt.split(';');
    wkt = split[1];
    dataProjection = `EPGS:${split[0].split('=')[1]}`
  }
  const feature = format.readFeature(wkt, {
    dataProjection: dataProjection,
    featureProjection: targetProjection,
  });
  return feature.getGeometry();
}
