import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { ModeStatistics, Scenario, TransportMode } from "../../../rest-interfaces";
import { PlanningService } from "../planning.service";

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
export class ModeSelectComponent {
  @Input() selected: TransportMode = TransportMode.WALK;
  @Input() label?: string;
  @Output() modeChanged = new EventEmitter<TransportMode>();
  TransportMode = TransportMode;
  modes = modes;
  Number = Number;
  modeStatus: Record<number, { enabled: boolean, message: string }> = {};
  _scenario?: Scenario;

  @Input() set scenario(scenario: Scenario | undefined){
    this._scenario = scenario;
    if (scenario === undefined)
      this.initModeStatus();
    else
      this.verifyModes();
  };

  constructor(private planningService: PlanningService) {
    this.initModeStatus();
  }

  changeMode(mode: TransportMode): void {
    this.selected = mode;
    this.modeChanged.emit(mode);
  }

  initModeStatus() {
    this.modeStatus = {};
    // enable all modes by default (stays this way until scenario is passed)
    Object.keys(modes).forEach(mode => {
      this.modeStatus[Number(mode)] = { enabled: true, message: ''};
    })
  }

  /**
   * check status of variant-modes of set scenario
   * flag mode as disabled (in disableModes) if either variant is not calculated or not set
   *
   * @param scenario
   */
  verifyModes(): void {
    this.modeStatus = {};
    if (!this._scenario) return;
    this.planningService.getRoutingStatistics().subscribe(stats => {
      for (let mode in this.modes) {
        const variant = this._scenario!.modeVariants.find(mv => mv.mode === Number(mode));
        if (!variant) {
          this.modeStatus[mode] = { enabled: false, message: 'Verkehrsmittelvariante ist nicht verfügbar' };
        }
        else {
          const nRels = stats.nRelsPlaceCellModevariant[variant.variant] || 0;
          this.modeStatus[mode] = { enabled: nRels > 0, message: (nRels === 0)? 'Verkehrsmittelvariante ist nicht berechnet': '' }
        }
      }
    })
  }
}
