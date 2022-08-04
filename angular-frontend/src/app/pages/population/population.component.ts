import { AfterViewInit, ChangeDetectorRef, Component, ViewChild } from '@angular/core';
import { MapControl, MapService } from "../../map/map.service";
import { faArrowsAlt } from '@fortawesome/free-solid-svg-icons';
import { TimeSliderComponent } from "../../elements/time-slider/time-slider.component";
import { PopulationService } from "./population.service";
import { Observable } from "rxjs";
import { map, shareReplay } from "rxjs/operators";
import { BreakpointObserver } from "@angular/cdk/layout";


@Component({
  selector: 'app-population',
  templateUrl: './population.component.html',
  styleUrls: ['./population.component.scss']
})
export class PopulationComponent implements AfterViewInit {
  @ViewChild('timeSlider') timeSlider?: TimeSliderComponent;
  mapControl?: MapControl;
  faArrows = faArrowsAlt;
  isLoading = true;
  mapDescription = '';
  isSM$: Observable<boolean> = this.breakpointObserver.observe('(max-width: 50em)')
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver, private mapService: MapService,
              public populationService: PopulationService, private cdref: ChangeDetectorRef) { }

  ngAfterViewInit(): void {
    this.mapControl = this.mapService.get('population-map');
    this.populationService.timeSlider = this.timeSlider;
    this.populationService.setReady(true);
    // using "isLoading$ | async" in template causes NG0100, because service doesn't know about life cycle of this page
    // workaround: force change detection
    this.populationService.isLoading$.subscribe(isLoading => {
      this.isLoading = isLoading;
      this.cdref.detectChanges();
    });
    // same as above
    this.mapControl.mapDescription$.subscribe(desc => {
      this.mapDescription = desc;
      this.cdref.detectChanges();
    });
  }

  ngOnDestroy(): void {
    this.mapControl?.destroy();
  }
}
