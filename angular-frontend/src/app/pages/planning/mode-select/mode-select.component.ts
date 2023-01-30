import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output
} from '@angular/core';
import { ModeStatistics, ModeVariant, Scenario, TransportMode } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";
import { Subscription } from "rxjs";

export const modes: Record<number, string> = {};
modes[TransportMode.WALK] = 'zu Fuß';
modes[TransportMode.BIKE] = 'Fahrrad';
modes[TransportMode.CAR] = 'Auto';
modes[TransportMode.TRANSIT] = 'ÖPNV';

@Component({
  selector: 'app-mode-select',
  templateUrl: './mode-select.component.html',
  styleUrls: ['./mode-select.component.scss']
})
export class ModeSelectComponent implements OnDestroy{
  @Input() label?: string;
  @Output() modeChanged = new EventEmitter<TransportMode | undefined>();
  TransportMode = TransportMode;
  modes = modes;
  Number = Number;
  modeStatus: Record<number, { enabled: boolean, message: string }> = {};
  scenario?: Scenario;
  selectedMode?: TransportMode;
  private subscriptions: Subscription[] = [];

  @Input() set selected(mode: TransportMode | undefined) {
    this.selectedMode = mode;
  }

  constructor(private planningService: PlanningService, private cdRef: ChangeDetectorRef) {
    this.subscriptions.push(this.planningService.activeScenario$.subscribe(scenario => {
      this.scenario = scenario;
      this.verifyModes();
    }));
  }

  /**
   * check status of variant-modes of set scenario
   * flag mode as disabled (in disableModes) if either variant is not calculated or not set
   *
   * @param scenario
   */
  verifyModes(): void {
    this.modeStatus = {};
    if (!this.scenario) return;
    this.planningService.getModeVariants().subscribe(variants => {
      console.log(variants);
      for (let mode in this.modes) {
        const scenarioVariant = this.scenario!.modeVariants.find(mv => mv.mode === Number(mode));
        if (!scenarioVariant) {
          this.modeStatus[mode] = { enabled: false, message: 'Verkehrsmittelvariante ist nicht verfügbar' };
        }
        else {
          const stats = variants.find(v => v.id === scenarioVariant.variant)?.statistics;
          const nRels = stats?.nRelsPlaceCellModevariant || 0;
          this.modeStatus[mode] = { enabled: nRels > 0, message: (nRels === 0)? 'Verkehrsmittelvariante ist nicht berechnet': '' }
        }
      }
      this.cdRef.detectChanges();
      console.log(this.modeStatus);
      if (this.selectedMode && !this.modeStatus[this.selectedMode]?.enabled) {
        this.changeMode(undefined);
      }
    })
  }

  changeMode(mode: TransportMode | undefined): void {
    this.selectedMode = mode;
    this.modeChanged.emit(this.selectedMode);
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(subscription => subscription.unsubscribe());
  }
}
