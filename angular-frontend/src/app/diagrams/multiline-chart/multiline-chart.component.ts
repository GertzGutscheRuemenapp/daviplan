import { AfterViewInit, Component, Input } from '@angular/core';
import * as d3 from 'd3';
import { StackedData } from "../stacked-barchart/stacked-barchart.component";

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
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() labels?: string[];
  @Input() drawLegend: boolean = true;
  @Input() xLabel?: string;
  @Input() yLabel?: string;
  @Input() width?: number;
  @Input() height?: number;

  private svg: any;
  private margin: {top: number, bottom: number, left: number, right: number } = {
    top: 50,
    bottom: 40,
    left: 60,
    right: 60
  };

  ngAfterViewInit(): void {
    this.createSvg();
    if (this.data) this.draw(this.data);
  }

  private createSvg(): void {
    let figure = d3.select("figure#multiline-chart");
    if (!(this.width && this.height)){
      let node: any = figure.node()
      let bbox = node.getBoundingClientRect();
      if (!this.width)
        this.width = bbox.width;
      if (!this.height)
        this.height = bbox.height;
    }
    this.svg = figure.append("svg")
      .attr("width", this.width!)
      .attr("height", this.height!)
      .append("g");
  }

  private draw(data: MultilineData[]): void {
    if (data.length == 0) return

    if (!this.labels)
      this.labels = d3.range(0, data[0].values.length).map(d=>d.toString());
    let colorScale = d3.scaleOrdinal(d3.schemeCategory10);
    let max = d3.max(data, d => { return d3.max(d.values) });
    let innerWidth = this.width! - this.margin.left - this.margin.right,
      innerHeight = this.height! - this.margin.top - this.margin.bottom;
    // Add X axis
    const x = d3.scaleBand()
      .range([0, innerWidth])
      .domain(data.map(d => d.group))
      .padding(0.5);

    // x axis
    this.svg.append("g")
      .attr("transform",`translate(${this.margin.left},${innerHeight + this.margin.top})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end");

    // y axis
    const y = d3.scaleLinear()
      .domain([0, max!])
      .range([innerHeight, 0]);

    this.svg.append("g")
      .attr("transform", `translate(${this.margin.left},${this.margin.top})`)
      .call(d3.axisLeft(y));

    if (this.yLabel)
      this.svg.append('text')
        .attr("y", 10)
        .attr("x", -(this.margin.top + 30))
        .attr('dy', '0.5em')
        .style('text-anchor', 'middle')
        .attr('transform', 'rotate(-90)')
        .attr('font-size', '0.8em')
        .text(this.yLabel);

    if (this.xLabel)
      this.svg.append('text')
        .attr("y", this.height! - 10)
        .attr("x", this.width! - this.margin.right)
        .attr('dy', '0.5em')
        .style('text-anchor', 'end')
        .attr('font-size', '0.8em')
        .text(this.xLabel);

    let _this = this;
    // tooltips
/*    function onMouseOverBar(this: any, event: MouseEvent) {
      let stack = d3.select(this);
      let data: StackedData = this.__data__;
      stack.selectAll('rect').classed('highlight', true);

      let tooltip = d3.select('body').append('div').attr('class', 'tooltip');
      let text = data.group.toString().replace('.',',') + '<br>';
      tooltip.style('opacity', .9);
      //
      _this.labels?.forEach((label, i)=>{
        text += label + ': <b>' + data.values[i].toString().replace('.',',') + '</b><br>';
      })
      // text += 'gesamt: <b>' + d.total.toString().replace('.',',') + '</b><br>';
      tooltip.html(text);
      tooltip.style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - parseInt(tooltip.style('height'))) + 'px');
    };

    function onMouseOutBar(this: any, event: MouseEvent) {
      let stack = d3.select(this);
      stack.selectAll('rect').classed('highlight', false);
      d3.select('body').selectAll('div.tooltip').remove();
    }*/
    let line = d3.line()
      .curve(d3.curveCardinal)
      .x((d: any) => x(d.group)!)
      .y((d: any) => y(d.value));

    this.labels.forEach((label, i)=>{

      let di = data.map(d => {
        return {
          group: d.group,
          value: d.values[i]
        }
      });
      this.svg.append('g')
        .attr("transform", `translate(${this.margin.left}, ${this.margin.top})`)
        .append("path")
        .datum(di)
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", colorScale(i.toString()))
        .attr("stroke-width", 1.5)
        .attr("d", line);
    })

    if (this.drawLegend) {
      let size = 15;

      this.svg.selectAll("legendRect")
        .data(this.labels.reverse())
        .enter()
        .append("rect")
        .attr("x", innerWidth + this.margin.left)
        .attr("y", (d: string, i: number) => 105 + (i * (size + 5))) // 100 is where the first dot appears. 25 is the distance between dots
        .attr("width", size)
        .attr("height", 3)
        .style("fill", (d: string, i: number) => colorScale(i.toString()));

      this.svg.selectAll("legendLabels")
        .data(this.labels.reverse())
        .enter()
        .append("text")
        .attr('font-size', '0.7em')
        .attr("x", innerWidth + this.margin.left + size * 1.2)
        .attr("y", (d: string, i: number) => 100 + (i * (size + 5) + (size / 2)))
        .style("fill", (d: string, i: number) => colorScale(i.toString()))
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
