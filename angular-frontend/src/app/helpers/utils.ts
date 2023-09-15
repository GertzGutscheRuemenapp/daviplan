import { WKT } from "ol/format";
import { Geometry } from "ol/geom";
import { MatDialog } from "@angular/material/dialog";
import { SimpleDialogComponent } from "../dialogs/simple-dialog/simple-dialog.component";

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

export function wktToGeom(wkt: string, options?: { targetProjection?: string, dataProjection?: string, ewkt?: boolean }): Geometry | undefined {
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

export function showMessage(message: string, dialog: MatDialog) {
  SimpleDialogComponent.show(message, dialog, {showConfirmButton: true, disableClose: true})
}

export function showAPIError(error: any, dialog: MatDialog) {
  const title = `Fehler ${error.status || ''}`;
  let message = '';
  if (error.status === 0)
    message = 'Server antwortet nicht';
  else if (error.error) {
    // usually the backend responds with a message (wrapped in error attribute)
    if (error.error.message)
      // style injection via innerHTML is not trusted, using class to color it red instead
      message = `<span class="red">${error.error.message}</span>`
    else if (typeof(error.error) === 'string'){
      message = error.error;
    }
    else {
      // Rest API responds to malformed requests with a list of fields and the corresponding error
      Object.keys(error.error).forEach(key => {
        message += `<p><b>${key.toUpperCase()}</b>: <span class="red">${error.error[key]}</span></p>`;
      })
    }
  }
  // fallback default message (in most cases very cryptic and not localized)
  else
    message = `<span class="red">${error.message}</span>`

  SimpleDialogComponent.show(message, dialog, {
    title: title, showConfirmButton: true, disableClose: true,
    centerContent: true
  })
}
