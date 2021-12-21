import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../../map/map.service";
import { InputCardComponent } from "../../../dash/input-card.component";
import { Geometry, GeometryCollection, MultiPolygon, Polygon } from "ol/geom";
import { Collection, Feature } from 'ol';
import { register } from 'ol/proj/proj4'
import union from '@turf/union';
import pointOnSurface from '@turf/point-on-surface';
import booleanWithin from "@turf/boolean-within";
import * as turf from '@turf/helpers';
import { GeoJSON, WKT } from "ol/format";
import proj4 from 'proj4';
import { HttpClient } from "@angular/common/http";
import { RestAPI } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { SiteSettings } from "../../../settings.service";
import { Observable } from "rxjs";
import { Layer } from "ol/layer";

export interface ProjectSettings {
  projectArea: string,
  startYear: number,
  endYear: number
}

export interface AgeGroup {
  id: number,
  fromAge: number,
  toAge: number
}

interface BKGLayer {
  name: string,
  tag: string
}

const areaLayers: BKGLayer[] = [
  { name: 'Kreise', tag: 'vg250_krs' },
  { name: 'Verwaltungsgebiete', tag: 'vg250_vwg' },
  { name: 'Gemeinden', tag: 'vg250_gem' },
]

proj4.defs("EPSG:25832", "+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs");
register(proj4);

@Component({
  selector: 'app-project-definition',
  templateUrl: './project-definition.component.html',
  styleUrls: ['./project-definition.component.scss']
})
export class ProjectDefinitionComponent implements AfterViewInit, OnDestroy {
  previewMapControl?: MapControl;
  areaSelectMapControl?: MapControl;
  projectGeom?: MultiPolygon;
  __projectGeom?: MultiPolygon;
  projectAreaFeature?: Feature<any>;
  ageGroups?: AgeGroup[];
  __ageGroups: AgeGroup[] = [];
  ageGroupDefaults: AgeGroup[] = [];
  projectAreaErrors = [];
  projectSettings?: ProjectSettings;
  yearForm!: FormGroup;
  Object = Object;
  areaLayers = areaLayers;
  selectedAreaLayer: BKGLayer = areaLayers[0];
  baseAreaLayer: BKGLayer = areaLayers[areaLayers.length - 1];
  private _baseSelectLayer?: Layer<any>;
  @ViewChild('areaCard') areaCard!: InputCardComponent;
  @ViewChild('yearCard') yearCard!: InputCardComponent;
  @ViewChild('ageGroupCard') ageGroupCard!: InputCardComponent;

  constructor(private mapService: MapService, private formBuilder: FormBuilder, private http: HttpClient,
              private rest: RestAPI) { }

  ngAfterViewInit(): void {
    this.setupPreviewMap();
    this.setupAreaCard();
    this.fetchProjectSettings().subscribe(settings => {
      this.setupYearCard();
      this.updatePreviewLayer();
    });
    this.fetchAgeGroups().subscribe(settings => {
      this.setupAgeGroupCard();
    });
  }

  fetchProjectSettings(): Observable<ProjectSettings> {
    let query = this.http.get<ProjectSettings>(this.rest.URLS.projectSettings);
    query.subscribe(projectSettings => {
      this.projectSettings = projectSettings;
    })
    return query;
  }

  fetchAgeGroups(): Observable<AgeGroup[]> {
    this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups, {params: {defaults: true}}).subscribe(ageGroups => {
      this.ageGroupDefaults = ageGroups;
    })
    let query = this.http.get<AgeGroup[]>(this.rest.URLS.ageGroups);
    query.subscribe(ageGroups => {
      this.ageGroups = ageGroups;
    })
    return query;
  }

  setupPreviewMap(): void {
    this.previewMapControl = this.mapService.get('project-preview-map');
    this.previewMapControl.setBackground(this.previewMapControl.getBackgroundLayers()[0].id);
    this.previewMapControl.map?.addVectorLayer('project-area',{
      visible: true,
      stroke: { color: 'red', width: 3 },
      fill: { color: 'rgba(255, 255, 0, 0.5)' }
    });
  }

  setupAgeGroupCard(): void {
    this.__ageGroups = this.ageGroups!;

    this.ageGroupCard.dialogConfirmed.subscribe(ok => {
      this.ageGroupCard.setLoading(true);
      this.__ageGroups.forEach(group => {

      })
    })
    this.yearCard.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
      }
    })
  }

  setupYearCard(): void {
    this.yearForm = this.formBuilder.group({
      startYear: this.projectSettings!.startYear,
      endYear: this.projectSettings!.endYear
    });
    this.yearCard.dialogConfirmed.subscribe(()=>{
      this.yearForm.setErrors(null);
      this.yearForm.markAllAsTouched();
      if (this.yearForm.invalid) return;
      const startYear = this.yearForm.value.startYear,
        endYear = this.yearForm.value.endYear;
      if (endYear <= startYear) {
        this.yearForm.controls['startYear'].setErrors({'tooHigh': true});
        return;
      }
      let attributes: any = {
        startYear: startYear,
        endYear: endYear
      }
      this.yearCard.setLoading(true);
      this.http.patch<ProjectSettings>(this.rest.URLS.projectSettings, attributes
      ).subscribe(settings => {
        this.yearCard.closeDialog(true);
        this.projectSettings = settings;
      },(error) => {
        // ToDo: set specific errors to fields
        this.yearForm.setErrors(error.error);
        this.yearCard.setLoading(false);
      });
    })
    this.yearCard.dialogClosed.subscribe((ok)=>{
      // reset form on cancel
      if (!ok){
        this.yearForm.reset({
          startYear: this.projectSettings!.startYear,
          endYear: this.projectSettings!.endYear
        });
      }
    })
  }

  updatePreviewLayer(){
    let previewLayer = this.previewMapControl?.map?.getLayer('project-area');
    if (previewLayer) {
      const format = new WKT();
      if (this.projectSettings!.projectArea) {
        const wktSplit = this.projectSettings!.projectArea.split(';'),
          epsg = wktSplit[0].replace('SRID=','EPSG:'),
          wkt = wktSplit[1];

        let feature = format.readFeature(wkt);
        feature.getGeometry().transform(epsg, `EPSG:${this.previewMapControl?.srid}`);
        this.projectGeom = feature.getGeometry();
        const source = previewLayer.getSource();
        source.clear();
        source.addFeature(feature);
        if (this.projectGeom?.getArea())
          this.previewMapControl?.map?.centerOnLayer('project-area');
      }
    }
  }

  setupAreaCard(): void {
    this.areaCard.dialogOpened.subscribe(x => {
      this.projectAreaErrors = [];
      // this.areaCard.setLoading(true);
      this.areaSelectMapControl = this.mapService.get('project-area-select-map');
      this.areaSelectMapControl.setBackground(this.areaSelectMapControl.getBackgroundLayers()[0].id)

      let projectLayer = this.areaSelectMapControl.map?.addVectorLayer('project-area', {
        stroke: { color: 'red', width: 3 },
        visible: true
      });
      this.projectAreaFeature = new Feature(this.projectGeom);
      projectLayer?.getSource().addFeature(this.projectAreaFeature);
      const hasProjectArea = this.projectGeom?.getArea();
      if (hasProjectArea)
        this.areaSelectMapControl.map?.centerOnLayer('project-area');
      this.areaSelectMapControl.map?.selected.subscribe(event => {
        this.featuresSelected(event.layer, event.selected, event.deselected);
      })
      const _this = this;

      this.areaLayers.forEach(al => {
        const layer = _this.areaSelectMapControl!.map?.addVectorLayer(
          al.tag, {
            url: function (extent: any) {
              return (
                'https://sgx.geodatenzentrum.de/wfs_vg250?service=WFS&' +
                `version=1.1.0&request=GetFeature&typename=${al.tag}&` +
                'outputFormat=application/json&srsname=EPSG:3857&' +
                'bbox=' +
                extent.join(',') +
                ',EPSG:3857'
              )},
            visible: al === _this.baseAreaLayer || al === _this.selectedAreaLayer,
            selectable: true,
            opacity: (al === _this.baseAreaLayer)? 0 : 0.5,
            tooltipField: 'gen',
            stroke: { color: 'black', selectedColor: 'rgba(0, 0, 0, 0)' },
            fill: { color: 'rgba(0, 0, 0, 0)', selectedColor: (al === _this.baseAreaLayer)? 'yellow': 'red' }
          });
        layer?.set('showTooltip', al === this.selectedAreaLayer);
        layer?.get('select').setActive(al === this.selectedAreaLayer);
      })
      this._baseSelectLayer = this.areaSelectMapControl.map?.getLayer(this.baseAreaLayer.tag);
      this._baseSelectLayer?.getSource().addEventListener('featuresloadstart', function () {
        _this.areaCard.setLoading(true);
      });
      let init = false;
      this._baseSelectLayer?.getSource().addEventListener('featuresloadend', function () {
        _this.areaCard.setLoading(false);
        if (init) return;
        init = true;
        if (!hasProjectArea) return;
        const select = _this._baseSelectLayer?.get('select');
        _this._baseSelectLayer?.getSource().getFeatures().forEach((feature: Feature<any>) => {
          let poss = feature.getGeometry().getInteriorPoints().getCoordinates();
          for (let i = 0; i < poss.length; i++) {
            let coords = poss[i],
                intersection = _this.projectGeom!.intersectsCoordinate(coords);
            if (intersection) {
              select.getFeatures().push(feature);
              break;
            }
          }
        })
      });
    })
    this.areaCard.dialogClosed.subscribe(x => {
      this.areaSelectMapControl?.destroy();
    })
    this.areaCard.dialogConfirmed.subscribe(ok => {
      const format = new WKT();
      let wkt = this.__projectGeom? `SRID=${this.areaSelectMapControl?.srid};` + format.writeGeometry(this.__projectGeom) : null
      this.http.patch<ProjectSettings>(`${this.rest.URLS.projectSettings}`,
        { projectArea: wkt }
      ).subscribe(settings => {
        this.areaCard?.closeDialog(true);
        this.projectSettings = settings;
        this.updatePreviewLayer();
      },(error) => {
        this.projectAreaErrors = error.error;
      });
    })
  }

  resetAgeGroups(): void {
    this.__ageGroups = Object.assign([], this.ageGroupDefaults);
  }

  changeAreaLayer(): void {
    const _this = this;
    this.areaLayers.forEach(al => {
      const layer = this.areaSelectMapControl?.map?.getLayer(al.tag);
      const select = layer?.get('select');
      if (al !== _this.baseAreaLayer) {
        layer?.setVisible(al === _this.selectedAreaLayer);
        select.getFeatures().clear();
      }
/*      else
        layer?.setOpacity((al === _this.selectedAreaLayer) ? 0.5 : 0);*/
      select.setActive(al === this.selectedAreaLayer);
      layer?.set('showTooltip', al === this.selectedAreaLayer);
    })
  }

  featuresSelected(layer: Layer<any>, selected: Feature<any>[], deselected: Feature<any>[]){
    if (layer !== this._baseSelectLayer){
      selected.forEach(feature => {
        let baseFeatures = feature.get('intersect');
        if (!baseFeatures) {
          baseFeatures = this.getBaseIntersections(feature);
          feature.set('intersect', baseFeatures);
        }
        this.areaSelectMapControl?.map?.selectFeatures(this.baseAreaLayer.tag, baseFeatures);
      })
    }
    else{
/*      let features = this._baseSelectLayer?.get('select').getFeatures();
      let mergedGeom: turf.Feature<turf.MultiPolygon | turf.Polygon> | null = null;
      features.forEach((f: Feature<any>) => {
        // const json = format.writeGeometryObject(f.getGeometry());
        const poly = turf.multiPolygon(f.getGeometry().getCoordinates());
        mergedGeom = mergedGeom ? union(poly, mergedGeom) : poly;
      })
      const format = new GeoJSON();
      // @ts-ignore
      this.__projectGeom = mergedGeom ? format.readFeature(mergedGeom.geometry).getGeometry() : new MultiPolygon([]);
      if (this.__projectGeom instanceof Polygon)
        // @ts-ignore
        this.__projectGeom = new MultiPolygon([this.__projectGeom.getCoordinates()]);
      this.projectAreaFeature?.setGeometry(this.__projectGeom);*/
    }
  }

  getBaseIntersections(feature: Feature<any>): Feature<any>[]{
    const _this = this;
    let intersecting: Feature<any>[] = [];
    this._baseSelectLayer?.getSource().getFeatures().forEach((baseFeature: Feature<any>) => {
      let poss = baseFeature.getGeometry().getInteriorPoints().getCoordinates();
      for (let i = 0; i < poss.length; i++) {
        let coords = poss[i],
          intersection = feature.getGeometry().intersectsCoordinate(coords);
        if (intersection) {
          intersecting.push(feature);
          break;
        }
      }
    })
    return intersecting;
  }

  ngOnDestroy(): void {
    this.previewMapControl?.destroy();
  }

}
