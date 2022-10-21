import { AfterViewInit, Component, Input } from '@angular/core';
import * as d3 from 'd3';
import { StackedData } from "../stacked-barchart/stacked-barchart.component";

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
  @Input() xLabel?: string;
  @Input() yLabel?: string;
  @Input() width?: number;
  @Input() margin: number = 20;
  @Input() height?: number;
  @Input() animate?: boolean;
  @Input() unit: string = '';
  @Input() figureId: String = 'horizontal-barchart';
  localeFormatter = d3.formatLocale({
    decimal: ',',
    thousands: '.',
    grouping: [3],
    currency: ['€', '']
  })
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
    this.svg = figure.append('svg')
      .attr('viewBox', `0 0 ${this.width!} ${this.height!}`);
  }

  clear(): void {
    this.svg.selectAll('*').remove();
  }

  draw(data: BarChartData[]): void {
    this.clear();
    if (data.length == 0) return;

    const barHeight = 20,
      barPadding = 5,
      max = d3.max(data, d => d.value) || 1;

    const height = (barHeight + barPadding) * data.length

    this.svg.attr('viewBox', `0 0 ${this.width!} ${height + this.margin * 2}`);

    const scale = d3.scaleLinear()
      .domain([0, max])
      .range([0, this.width! - this.margin*2]);
    console.log(data)

    this.svg.append('g')
      .attr('class', 'axis x right')
      .attr('transform', `translate(${this.margin}, ${this.margin})`)
      .call(
        d3.axisBottom(scale)
          .ticks(5)
          .tickSize(height)
          .tickFormat(d3.format('d'))
      );

    // tooltips
    function onMouseOverBar(this: any, event: MouseEvent) {
      let bar = d3.select(this);
      bar.select('rect').classed('highlight', true);
      const data = this.__data__;
      const formatter = _this.localeFormatter.format(',.2f');
      let text = `<b>${data.label}</b><br>${formatter(data.value)} ${_this.unit}`;
      tooltip.style('display', null);
      tooltip.html(text);
    };

    function onMouseOutBar(this: any, event: MouseEvent) {
      bar.select('rect').classed('highlight', false);
      tooltip.style('display', 'none');
    }

    function onMouseMove(this: any, event: MouseEvent){
      tooltip.style('left', event.pageX + 20 + 'px')
        .style('top', event.pageY + 10 + 'px');
    }

    const bar = this.svg.append('g').selectAll('g')
      .data(data)
      .enter()
      .append('g');

    bar.attr('class', 'bar')
      .attr('cx',0)
      .attr('transform', (d: BarChartData, i: number) => `translate(${this.margin}, ${i * (barHeight + barPadding) + barPadding})`)
      .on('mouseover', onMouseOverBar)
      .on('mouseout', onMouseOutBar)
      .on('mousemove', onMouseMove);

    bar.append('rect')
      // .attr('transform', 'translate('+labelWidth+', 0)')
      .style('fill', '#6daf56')
      .attr('height', barHeight)
      .attr('width', (d: BarChartData) => scale(d.value));

    bar.append('text')
      .attr('class', 'label')
      .attr('y', barHeight / 2)
      .attr('dy', '.35em') //vertical align middle
      .style('text-shadow', '-1px -1px white, -1px 1px white, 1px 1px white, 1px -1px white, -1px 0 white, 0 1px white, 1px 0 white, 0 -1px white')
      .text((d: BarChartData) => d.label);


    let tooltip = d3.select('body')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style('display', 'none');

    let _this = this;

  }

  ngOnInit(): void {
  }

}
