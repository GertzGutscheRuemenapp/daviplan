import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { TransportMode } from "../../../rest-interfaces";

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
export class ModeSelectComponent implements OnInit {
  @Input() mode: TransportMode = TransportMode.WALK;
  @Output() modeChanged = new EventEmitter<TransportMode>();
  TransportMode = TransportMode;
  modes = modes;
  Number = Number;

  constructor() { }

  changeMode(mode: TransportMode): void {
    this.mode = mode;
    this.modeChanged.emit(mode);
  }

  ngOnInit(): void {
  }

}
