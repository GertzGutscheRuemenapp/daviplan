import { AfterViewInit, Component, Input } from '@angular/core';
import * as d3 from "d3";

export interface BarChartData {
  label: string,
  value: number
}

@Component({
  selector: 'app-horizontal-barchart',
  templateUrl: './horizontal-barchart.component.html',
  styleUrls: ['./horizontal-barchart.component.scss']
})
export class HorizontalBarchartComponent implements AfterViewInit {
  @Input() data?: BarChartData[];
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() drawLegend: boolean = true;
  @Input() xLabel?: string;
  @Input() yLabel?: string;
  @Input() width?: number;
  @Input() height?: number;
  @Input() animate?: boolean;
  @Input() figureId: String = 'horizontal-barchart';
  private svg: any;

  constructor() { }

  ngAfterViewInit(): void {
    this.createSvg();
    if (this.data) this.draw(this.data);
  }

  private createSvg(): void {
    let figure = d3.select(`figure#${ this.figureId }`);
    if (!(this.width && this.height)){
      let node: any = figure.node()
      let bbox = node.getBoundingClientRect();
      if (!this.width)
        this.width = bbox.width;
      if (!this.height)
        this.height = bbox.height;
    }
    this.svg = figure.append("svg")
      .attr("viewBox", `0 0 ${this.width!} ${this.height!}`)
      .append("g");
  }

  clear(): void {
    this.svg.selectAll("*").remove();
  }

  draw(data: BarChartData[]): void {
    console.log(data);
    this.clear();
    if (data.length == 0) return;

    const margin = 40,
      valueMargin = 4,
      barHeight = 20,
      barPadding = 5,
      max = d3.max(data, d => d.value) || 0;
    let labelWidth = 0;

    const bar = this.svg.selectAll("g")
      .data(data)
      .enter()
      .append("g");

    bar.attr("class", "bar")
      .attr("cx",0)
      .attr("transform", (d: BarChartData, i: number) => `translate(${margin}, ${i * (barHeight + barPadding) + barPadding})`);

    const scale = d3.scaleLinear()
      .domain([0, max])
      .range([0, this.width! - margin*2]);

    bar.append("rect")
      // .attr("transform", "translate("+labelWidth+", 0)")
      .style("fill", '#6daf56')
      .attr("height", barHeight)
      .attr("width", (d: BarChartData) => scale(d.value));

    bar.append("text")
      .attr("class", "label")
      .attr("y", barHeight / 2)
      .attr("dy", ".35em") //vertical align middle
      .style('text-shadow', '-1px -1px white, -1px 1px white, 1px 1px white, 1px -1px white, -1px 0 white, 0 1px white, 1px 0 white, 0 -1px white')
      .text((d: BarChartData) => d.label
      ).each(() => {
        labelWidth = Math.ceil(Math.max(labelWidth, this.width!))
      });

    // const xAxis = d3.axisBottom()
    //   .scale(scale)
    //   .tickSize(-height + 2*margin + axisMargin)
    //   .orient("bottom");

    bar.append("text")
      .attr("class", "value")
      .attr("y", barHeight / 2)
      .attr("dx", -valueMargin + labelWidth) //margin right
      .attr("dy", ".35em") //vertical align middle
      .attr("text-anchor", "end")
      .text( (d: BarChartData) => d.value)
      .attr("x", (d: BarChartData) => Math.max(this.width! + valueMargin, scale(d.value)));
  }

  ngOnInit(): void {
  }

}
