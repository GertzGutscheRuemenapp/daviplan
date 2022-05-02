import { AfterViewInit, Component, Input } from '@angular/core';
import * as d3 from 'd3';
import { v4 as uuid } from "uuid";

export interface MultilineData {
  group: string,
  values: number[]
}

@Component({
  selector: 'app-multiline-chart',
  templateUrl: './multiline-chart.component.html',
  styleUrls: ['./multiline-chart.component.scss']
})
export class MultilineChartComponent implements AfterViewInit {

  @Input() data?: MultilineData[];
  @Input() figureId: String = `figure${uuid()}`;
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() labels?: string[];
  @Input() drawLegend: boolean = true;
  @Input() xLabel?: string;
  @Input() yLabel?: string;
  @Input() yTicks?: number;
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
  @Input() xLegendOffset: number = 70;
  @Input() yLegendOffset: number = 0;
  @Input() animate?: boolean;
  @Input() xSeparator?: { leftLabel?: string, rightLabel?:string, x: string, highlight?: boolean };
  @Input() shiftXLabelDown?: boolean;

  private svg: any;
  @Input() margin: {top: number, bottom: number, left: number, right: number } = {
    top: 50,
    bottom: 50,
    left: 60,
    right: 130
  };

  localeFormatter = d3.formatLocale({
    decimal: ',',
    thousands: '.',
    grouping: [3],
    currency: ['€', '']
  })

  ngAfterViewInit(): void {
    this.createSvg();
    if (this.data) this.draw(this.data);
  }

  private createSvg(): void {
    let figure = d3.select(`figure#${this.figureId}`);
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

  public draw(data: MultilineData[]): void {
    this.clear();
    if (data.length == 0) return;

    if (!this.labels)
      this.labels = d3.range(0, data[0].values.length).map(d=>d.toString());
    let colorScale = d3.scaleSequential().domain([0, this.labels.length])
      .interpolator(d3.interpolateRainbow);
    let innerWidth = this.width! - this.margin.left - this.margin.right,
      innerHeight = this.height! - this.margin.top - this.margin.bottom;
    let groups = data.map(d => d.group);
    // Add X axis
    const x = d3.scaleBand()
      .range([0, innerWidth])
      .domain(groups)
      .padding(0);

    let max = this.max || d3.max(data, d => { return d3.max(d.values) });
    max! += this.yPadding;
    let min = (this.min === undefined)? d3.min(data, d => { return d3.min(d.values) }): this.min;
    min! -= this.yPadding;
    const y = d3.scaleLinear()
      .domain([min!, max!])
      .range([innerHeight, 0]);

    const nthTick: number | undefined = (this.yTicks !== undefined)? Math.floor(data.length / this.yTicks) : undefined;

    // x axis
    this.svg.append("g")
      .attr("transform",`translate(${this.margin.left},${this.margin.top + y(this.yOrigin)})`)
      .call(d3.axisBottom(x).tickFormat((x: any, i: number) => (nthTick && i % nthTick !== 0)? '': x))
      .selectAll("text")
      .attr("transform", `translate(-10,${this.shiftXLabelDown? y(min!) - y(this.yOrigin): 0})rotate(-45)`)
      .style("text-anchor", "end");

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
        .attr("y", this.shiftXLabelDown? this.margin.top + y(min!): this.margin.top + y(this.yOrigin) + 20)
        .attr("x", this.width! - this.margin.right + 10)
        .attr('dy', '0.5em')
        .style('text-anchor', 'middle')
        .attr('font-size', '0.8em')
        .text(this.xLabel);

    let line = d3.line()
      // .curve(d3.curveCardinal)
      .x((d: any) => x(d.group)!)
      .y((d: any) => y(d.value));

    let _this = this;

    let tooltip = d3.select('body')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style("display", 'none');

    let lineG = this.svg.append('g')
      .attr("transform", `translate(${this.margin.left + x.bandwidth()/2}, ${this.margin.top})`)
      .on("mouseover", () => {
        lineG.selectAll('circle').style("display", null);
        tooltip.style("display", null);
      })
      .on("mouseout", () => {
        lineG.selectAll('circle').style("display", 'none');
        tooltip.style("display", 'none');
      })
      .on("mousemove", onMouseMove);

    // helper rect to enlarge g for catching mouse moves
    lineG.append('rect')
      .attr("height", innerHeight)
      .attr("width", innerWidth)
      .attr("opacity", '0')

    function onMouseMove(this: any, event: MouseEvent){
      let xPos = d3.pointer(event)[0],
          xIdx = Math.floor((xPos + x.bandwidth()/2) / x.bandwidth()),
          groupData = data![xIdx];
      if (!groupData) return;
      lineG.selectAll('circle')
        .transition()
        .duration(this.animate ? 60 : 0)
        .attr("transform", (d: null, i: number) => `translate(${x(groups[xIdx])}, ${y(groupData.values[i])})`);
      let text = `<b>${groupData.group}</b><br>`;
      const formatter = _this.localeFormatter.format(',.2f');
      _this.labels?.slice().reverse().forEach((label, i)=>{
        const j = _this.labels!.length - i - 1;
        let color = (_this.colors)? _this.colors[j]: colorScale(j);
        text += `<b style="color: ${color}">${label}</b>: ${formatter(groupData.values[j])}${(_this.unit)? _this.unit : ''}<br>`;
      })
      tooltip.html(text);
      tooltip.style('left', event.pageX - 70 + 'px')
        .style('top', event.pageY + 20 + 'px');
    }

    this.labels.forEach((label, i)=>{

      let di = data.map(d => {
        return {
          group: d.group,
          value: d.values[i]
        }
      });
      let path = lineG.append("path")
        .datum(di)
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", (this.colors)? this.colors[i]: colorScale(i))
        .attr("stroke-width", 3)
        .attr("d", line);

      if (this.animate) {
        let length = path.node().getTotalLength();
        path.attr("stroke-dasharray", length + " " + length)
          .attr("stroke-dashoffset", length)
          .transition()
          .duration(1000)
          // .ease(d3.easeQuadOut)
          .attr("stroke-dashoffset", 0);
      }

      lineG.append("circle")
        .attr("r", 3)
        .attr("fill", (this.colors)? this.colors[i]: colorScale(i))
        .style("display", 'none');
    })

    if (this.drawLegend) {
      let size = 15;

      this.svg.selectAll("legendRect")
        .data(this.labels.slice().reverse())
        .enter()
        .append("rect")
        .attr("x", innerWidth + this.xLegendOffset)
        .attr("y", (d: string, i: number) => 10 + this.yLegendOffset + (i * (size + 1)))
        .attr("width", size)
        .attr("height", 3)
        .style("fill", (d: string, i: number) => {
          const j = this.labels!.length - i - 1;
          return (this.colors) ? this.colors[j] : colorScale(j)
        })

      this.svg.selectAll("legendLabels")
        .data(this.labels.slice().reverse())
        .enter()
        .append("text")
        .attr('font-size', '0.7em')
        .attr("x", innerWidth + this.xLegendOffset + size * 1.2)
        .attr("y", (d: string, i: number) => 5 + this.yLegendOffset + (i * (size + 1) + (size / 2)))
        .style("fill", (d: string, i: number) => {
          const j = this.labels!.length - i - 1;
          return (this.colors) ? this.colors[j] : colorScale(j)
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

    if (this.xSeparator) {
      let xSepPos = x(this.xSeparator.x)! + this.margin.left + x.bandwidth();
      this.svg.append('line')
        // .style('stroke', 'grey')
        .attr('x1', xSepPos)
        .attr('y1', this.margin.top)
        .attr('x2', xSepPos)
        .attr('y2', this.height)
        .attr('class', 'separator');
      if (this.xSeparator.leftLabel)
        this.svg.append('text')
          .attr("y", this.height! - 10)
          .attr("x", xSepPos - 5)
          .attr('dy', '0.5em')
          .style('text-anchor', 'end')
          .attr('font-size', '0.7em')
          .attr('fill', 'grey')
          .text(this.xSeparator.leftLabel);
      if (this.xSeparator.rightLabel)
        this.svg.append('text')
          .attr("y", this.height! - 10)
          .attr("x", xSepPos + 5)
          .attr('dy', '0.5em')
          .style('text-anchor', 'start')
          .attr('font-size', '0.7em')
          .attr('fill', 'grey')
          .text(this.xSeparator.rightLabel);
      if (this.xSeparator.highlight) {
        this.svg.append('rect')
          .attr("x", xSepPos)
          .attr("y", this.margin.top - 10) // 100 is where the first dot appears. 25 is the distance between dots
          .attr("width", innerWidth - x(this.xSeparator.x)! - x.bandwidth())
          .attr("height", innerHeight + 10)
          .attr("fill", 'white')
          .attr("opacity", 0.5)
          .attr('pointer-events', 'none')
      }
    }
  }
}
