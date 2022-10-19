import { Component, Input, OnInit } from '@angular/core';

export interface BarChartData {
  groups: string[],
  values: number[]
}

@Component({
  selector: 'app-vertical-barchart',
  templateUrl: './vertical-barchart.component.html',
  styleUrls: ['./vertical-barchart.component.scss']
})
export class VerticalBarchartComponent implements OnInit {
  @Input() data?: BarChartData;
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() colors?: string[];
  @Input() drawLegend: boolean = true;
  @Input() xLabel?: string;
  @Input() yLabel?: string;
  @Input() width?: number;
  @Input() height?: number;
  @Input() animate?: boolean;

  constructor() { }

  ngOnInit(): void {
  }

}
