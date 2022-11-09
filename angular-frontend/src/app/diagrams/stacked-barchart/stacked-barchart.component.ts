import { AfterViewInit, Component, Input } from '@angular/core';
import * as d3 from 'd3';
import { DiagramComponent } from "../diagram/diagram.component";

export interface StackedData {
  group: string,
  values: number[]
}

@Component({
  selector: 'app-stacked-barchart',
  templateUrl: '../diagram/diagram.component.html',
  styleUrls: ['./stacked-barchart.component.scss', '../diagram/diagram.component.scss']
})
export class StackedBarchartComponent extends DiagramComponent implements AfterViewInit {

  @Input() data?: StackedData[];
  @Input() labels?: string[];
  @Input() colors?: string[];
  @Input() drawLegend: boolean = true;
  @Input() xLegendOffset: number = 70;
  @Input() yLegendOffset: number = 20;
  @Input() xLabel?: string;
  @Input() yLabel?: string;
  @Input() animate?: boolean;
  @Input() xSeparator?: { leftLabel?: string, rightLabel?:string, x: string, highlight?: boolean };
  private margin: {top: number, bottom: number, left: number, right: number } = {
    top: 50,
    bottom: 50,
    left: 60,
    right: 130
  };

  ngAfterViewInit(): void {
    this.createSvg();
    if (this.data) this.draw(this.data);
  }

  draw(data: StackedData[]): void {
    this.clear();
    if (data.length == 0) return;

    if (!this.labels)
      this.labels = d3.range(0, data[0].values.length).map(d=>d.toString());
    let colorScale = d3.scaleSequential().domain([0, this.labels.length])
      .interpolator(d3.interpolateRainbow);
    let max = d3.max(data, d => { return d.values.reduce((a, c) => a + c) });
    let innerWidth = this.width! - this.margin.left - this.margin.right,
        innerHeight = this.height! - this.margin.top - this.margin.bottom;

    let groups = data.map(d => d.group);
    // Add X axis
    const x = d3.scaleBand()
      .range([0, innerWidth])
      .domain(groups)
      .padding(0.5);

    // x axis
    this.svg.append('g')
      .attr('transform',`translate(${this.margin.left},${innerHeight + this.margin.top})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'translate(-10,0)rotate(-45)')
      .style('text-anchor', 'end');

    // y axis
    const y = d3.scaleLinear()
      .domain([0, max!])
      .range([innerHeight, 0]);

    this.svg.append('g')
      .attr('transform', `translate(${this.margin.left},${this.margin.top})`)
      .call(d3.axisLeft(y));

    if (this.yLabel)
      this.svg.append('text')
        .attr('y', 10)
        .attr('x', -(this.margin.top + 30))
        .attr('dy', '0.5em')
        .style('text-anchor', 'end')
        .attr('transform', 'rotate(-90)')
        .attr('font-size', '0.8em')
        .text(this.yLabel);

    if (this.xLabel)
      this.svg.append('text')
        .attr('y', this.height! - 30)
        .attr('x', this.width! - this.margin.right + 10)
        .attr('dy', '0.5em')
        .style('text-anchor', 'end')
        .attr('font-size', '0.8em')
        .text(this.xLabel);

    let tooltip = d3.select('body')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style('display', 'none');

    let _this = this;
    // tooltips
    function onMouseOverBar(this: any, event: MouseEvent) {
      let stack = d3.select(this);
      stack.attr('opacity', 1);
      let data: StackedData = this.__data__;
      stack.selectAll('rect').classed('highlight', true);
      let text = `<b>${data.group}</b><br>`;
      _this.labels?.slice().reverse().forEach((label, i)=>{
        const j = _this.labels!.length - i - 1;
        let color = (_this.colors)? _this.colors[j]: colorScale(j);
        text += `<b style='color: ${color}'>${label}</b>: ${data.values[j].toLocaleString()}<br>`;
      })
      tooltip.style('display', null);
      tooltip.html(text);
    };

    let sepIdx = (this.xSeparator) ? groups.indexOf(this.xSeparator.x) : -1;
    function highlightOpacity(i: number) {
      return _this.xSeparator && _this.xSeparator.highlight && i > sepIdx ? 0.7 : 1;
    }

    function onMouseOutBar(this: any, event: MouseEvent) {
      let stack = d3.select(this);
      let data: StackedData = this.__data__;
      stack.attr('opacity', highlightOpacity(groups.indexOf(data.group)));
      stack.selectAll('rect').classed('highlight', false);
      tooltip.style('display', 'none');
    }

    function onMouseMove(this: any, event: MouseEvent){
      tooltip.style('left', event.pageX + 20 + 'px')
        .style('top', event.pageY + 10 + 'px');
    }

    // stacked bars
    let bars = this.svg.selectAll('stacks')
      .data(data)
      .enter().append('g')
        // .attr('x', (d: StackedData) => x(d.year.toString()))
        .attr('transform', (d: StackedData) => `translate(${x(d.group)! + this.margin.left}, ${this.margin.top})`)
        .on('mouseover', onMouseOverBar)
        .on('mouseout', onMouseOutBar)
        .on('mousemove', onMouseMove)
        .attr('opacity', (d: StackedData, i: number) => highlightOpacity(i))
        .selectAll('rect')
        .data((d: StackedData) => {
          // stack by summing up every element with its predecessors
          let stacked = d.values.map((v, i) => d.values.slice(0, i+1).reduce((a, b) => a + b));
          // draw highest bars first
          return stacked.reverse();
        })
        .enter().append('rect')
          .attr('width', x.bandwidth())
          .attr('fill', (d: number, i: number) => {
            // stacked data is reverse
            const j = data[0].values.length - i - 1;
            return (this.colors) ? this.colors[j] : colorScale(j);
          })
          .attr('y', (d: number) => (this.animate) ? innerHeight : y(d))
          .attr('height', (d: number) => (this.animate) ? innerHeight - y(0) : innerHeight - y(d));

    if (this.animate)
      bars.transition()
        .duration(800)
        .attr('y', (d: number) => y(d))
        .attr('height', (d: number) => innerHeight - y(d));
        // .delay((d: any, i: number) => i * 100);

    if (this.drawLegend) {
      let size = 15;

      this.svg.selectAll('legendRect')
        .data(this.labels.slice().reverse())
        .enter()
        .append('rect')
        .attr("x", innerWidth + this.xLegendOffset)
        .attr("y", (d: string, i: number) => 10 + this.yLegendOffset + (i * (size + 1)))
        .attr('width', size)
        .attr('height', size)
        .style('fill', (d: string, i: number) => {
          const j = this.labels!.length - i - 1;
          return (this.colors) ? this.colors[j] : colorScale(j);
        });

      this.svg.selectAll('legendLabels')
        .data(this.labels.slice().reverse())
        .enter()
        .append('text')
        .attr('font-size', '0.7em')
        .attr("x", innerWidth + this.xLegendOffset + size * 1.2)
        .attr("y", (d: string, i: number) => 5 + this.yLegendOffset + (i * (size + 1) + (size / 2)))
        .style('fill', (d: string, i: number) => {
          const j = this.labels!.length - i - 1;
          return (this.colors) ? this.colors[j] : colorScale(j);
        })
        .text((d: string) => d)
        .attr('text-anchor', 'left')
        .style('alignment-baseline', 'middle')
    }

    this.svg.append('text')
        .attr('class', 'title')
        .attr('x', this.margin.left)
        .attr('y', 15)
        .text(this.title);

    this.svg.append('text')
        .attr('class', 'subtitle')
        .attr('x', this.margin.left)
        .attr('y', 15)
        .attr('font-size', '0.8em')
        .attr('dy', '1em')
        .text(this.subtitle);

    if (this.xSeparator) {
      let xSepPos = x(this.xSeparator.x)! + this.margin.left + x.bandwidth() * 1.5;
      this.svg.append('line')
        // .style('stroke', 'black')
        .attr('x1', xSepPos)
        .attr('y1', this.margin.top)
        .attr('x2', xSepPos)
        .attr('y2', this.height)
        .attr('class', 'separator');
      if (this.xSeparator.leftLabel)
        this.svg.append('text')
          .attr('y', this.height! - 10)
          .attr('x', xSepPos - 5)
          .attr('dy', '0.5em')
          .style('text-anchor', 'end')
          .attr('font-size', '0.7em')
          .attr('fill', 'grey')
          .text(this.xSeparator.leftLabel);
      if (this.xSeparator.rightLabel)
        this.svg.append('text')
          .attr('y', this.height! - 10)
          .attr('x', xSepPos + 5)
          .attr('dy', '0.5em')
          .style('text-anchor', 'start')
          .attr('font-size', '0.7em')
          .attr('fill', 'grey')
          .text(this.xSeparator.rightLabel);
    }
  }
}
