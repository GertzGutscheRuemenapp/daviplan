import { AfterViewInit, Component, Input } from '@angular/core';
import * as d3 from "d3";
import { StackedData } from "../stacked-barchart/stacked-barchart.component";

export interface BalanceChartData {
  group: string,
  values: [number, number]
}

@Component({
  selector: 'app-balance-chart',
  templateUrl: './balance-chart.component.html',
  styleUrls: ['./balance-chart.component.scss']
})
export class BalanceChartComponent implements AfterViewInit {

  @Input() data?: BalanceChartData[];
  @Input() figureId: String = 'balance-chart';
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() labels?: string[];
  @Input() drawLegend: boolean = true;
  @Input() xLabel?: string;
  @Input() yLabel?: string;
  @Input() lineLabel: string = '';
  @Input() lineColor: string = 'blue';
  @Input() yTopLabel?: string;
  @Input() yBottomLabel?: string;
  @Input() width?: number;
  @Input() height?: number;
  @Input() unit?: string;
  @Input() min?: number;
  @Input() max?: number;
  @Input() colors?: string[];
  @Input() yPadding: number = 0;
  @Input() yOrigin: number = 0;
  @Input() animate?: boolean;

  private svg: any;
  public margin: {top: number, bottom: number, left: number, right: number } = {
    top: 50,
    bottom: 50,
    left: 60,
    right: 60
  };

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

  public clear(): void {
    this.svg.selectAll("*").remove();
  }

  public draw(data: BalanceChartData[]): void {
    this.clear();
    if (data.length == 0) return

    if (!this.labels)
      this.labels = d3.range(0, data[0].values.length).map(d=>d.toString());
    this.labels = this.labels.concat(this.lineLabel);
    let colorScale = d3.scaleOrdinal(d3.schemeSet2);
    let innerWidth = this.width! - this.margin.left - this.margin.right,
      innerHeight = this.height! - this.margin.top - this.margin.bottom;
    let groups = data.map(d => d.group);
    // Add X axis
    const x = d3.scaleBand()
      .range([0, innerWidth])
      .domain(groups)
      .padding(0.5);

    let max = this.max || d3.max(data, d => { return d3.max(d.values) });
    max! += this.yPadding;
    let min = this.min || d3.min(data, d => { return d3.min(d.values) });
    min! -= this.yPadding;
    const y = d3.scaleLinear()
      .domain([min!, max!])
      .range([innerHeight, 0]);
    let _this = this;
    let lineG: any;

    // tooltips
    let tooltip = d3.select('body')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style("display", 'none');

    function onMouseOverBar(this: any, event: MouseEvent) {
      let stack = d3.select(this);
      stack.attr("opacity", 1);
      let data: StackedData = this.__data__;
      let sum = data.values[0] + data.values[1];

      lineG.selectAll('circle')
        .style("display", null)
        .attr("transform", (d: null, i: number) => `translate(${x(data.group)}, ${y(sum)})`);

      stack.selectAll('rect').classed('highlight', true);
      let text = `<b>${data.group}</b><br>`;
      _this.labels?.forEach((label, i)=>{
        let color = (i === 2)? _this.lineColor: (_this.colors)? _this.colors[i]: colorScale(i.toString());
        let value = (i === 2)? sum: data.values[i];
        text += `<b style="color: ${color}">${label}</b>: ${value.toString().replace('.', ',')}<br>`;
      })
      tooltip.style("display", null);
      tooltip.html(text);
    };

    function onMouseOutBar(this: any, event: MouseEvent) {
      let stack = d3.select(this);
      let data: StackedData = this.__data__;
      stack.selectAll('rect').classed('highlight', false);
      tooltip.style("display", 'none');
      lineG.selectAll('circle')
        .style("display", 'none');
    }

    function onMouseMove(this: any, event: MouseEvent){
      tooltip.style('left', event.pageX - 30 + 'px')
        .style('top', event.pageY + 20 + 'px');
    }

    // stacked bars
    let bars = this.svg.selectAll("stacks")
      .data(data)
      .enter().append("g")
      // .attr("x", (d: StackedData) => x(d.year.toString()))
      .attr("transform", (d: BalanceChartData) => `translate(${x(d.group)! + this.margin.left}, ${this.margin.top})`)
      .on("mouseover", onMouseOverBar)
      .on("mouseout", onMouseOutBar)
      .on("mousemove", onMouseMove)
      .selectAll("rect")
      .data((d: BalanceChartData) => {
        return d.values;
      })
      .enter().append("rect")
      .attr("width", x.bandwidth())
      .attr("fill", (d: number, i: number) => (this.colors)? this.colors[i]: colorScale(i.toString()))
      .attr("y", (d: number, i: number) => {
        if (i === 0 && !this.animate)
          return y(d);
        return y(0);
      })
      .attr("height", (d: number, i: number) => {
        if (this.animate) return 0;
        if (i === 0)
          return y(0) - y(d);
        return y(d) - y(0);
      });

    if (this.animate)
      bars.transition()
          .duration(800)
          .attr("y", (d: number, i: number) => {
            if (i === 0)
              return y(d);
            return y(0);
          })
          .attr("height", (d: number, i: number) => {
            if (i === 0)
              return y(0) - y(d);
            return y(d) - y(0);
          });

    // x axis
    this.svg.append("g")
      .attr("transform",`translate(${this.margin.left},${this.margin.top + y(this.yOrigin)})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end")
      .style("pointer-events", "none")
      .style("text-shadow", "white 1px 1px 0px, white -1px 0px 0px")

    // y axis
    this.svg.append("g")
      .attr("transform", `translate(${this.margin.left},${this.margin.top})`)
      .call(
        d3.axisLeft(y)
          .tickFormat((y: any) => (this.unit) ? `${y}${this.unit}` : y)
      );

    if (this.yLabel)
      this.svg.append('text')
        .attr("y", 10)
        .attr("x", -(this.margin.top + 50))
        .attr('dy', '0.5em')
        .style('text-anchor', 'end')
        .attr('transform', 'rotate(-90)')
        .attr('font-size', '0.8em')
        .text(this.yLabel);

    if (this.yTopLabel)
      this.svg.append('text')
        .attr("x", 0)
        .attr("y", this.margin.top - 5)
        .style('text-anchor', 'start')
        .attr('font-size', '0.8em')
        .text(this.yTopLabel);

    if (this.yBottomLabel)
      this.svg.append('text')
        .attr("x", 0)
        .attr("y", y(min!) + this.margin.top + 15)
        .style('text-anchor', 'start')
        .attr('font-size', '0.8em')
        .text(this.yBottomLabel);

    if (this.xLabel)
      this.svg.append('text')
        .attr("y", this.margin.top + y(this.yOrigin) + 20)
        .attr("x", this.width! - this.margin.right + 10)
        .attr('dy', '0.5em')
        .style('text-anchor', 'end')
        .attr('font-size', '0.8em')
        .text(this.xLabel);

    let sums = data.map(d => {
      return {
        group: d.group,
        value: d.values[0] + d.values[1]
      }
    });
    let line = d3.line()
      .x((d: any) => x(d.group)!)
      .y((d: any) => y(d.value));

    lineG = this.svg.append('g')
      .attr("transform", `translate(${this.margin.left + x.bandwidth()/2}, ${this.margin.top})`);

    let path = lineG.append("path")
      .datum(sums)
      .attr("class", "line")
      .style("pointer-events", "none")
      .attr("fill", "none")
      .attr("stroke", this.lineColor)
      .attr("stroke-width", 3)
      .attr("d", line);

    lineG.append("circle")
      .datum(sums)
      .attr("r", 3)
      .attr("fill", this.lineColor)
      .style("display", 'none');

    if (this.animate) {
      let length = path.node().getTotalLength();
      path.attr("stroke-dasharray", length + " " + length)
        .attr("stroke-dashoffset", length)
        .transition()
        .duration(1000)
        .attr("stroke-dashoffset", 0);
    }

    if (this.drawLegend) {
      let size = 15;

      this.svg.selectAll("legendRect")
        .data(this.labels.reverse())
        .enter()
        .append("rect")
        .attr("x", innerWidth)
        .attr("y", (d: string, i: number) => 25 + (i * (size + 5)))
        .attr("width", size)
        .attr("height", 3)
        .style("fill", (d: string, i: number) => {
          if (i == 2) return this.lineColor;
          return (this.colors) ? this.colors[i] : colorScale(i.toString())
        });

      this.svg.selectAll("legendLabels")
        .data(this.labels.reverse())
        .enter()
        .append("text")
        .attr('font-size', '0.7em')
        .attr("x", innerWidth + size * 1.2)
        .attr("y", (d: string, i: number) => 20 + (i * (size + 5) + (size / 2)))
        .style("fill", (d: string, i: number) => {
          if (i == 2) return this.lineColor;
          return (this.colors) ? this.colors[i] : colorScale(i.toString())
        })
        .text((d: string) => d)
        .attr("text-anchor", "left")
        .style("alignment-baseline", "middle")
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

  }
}
