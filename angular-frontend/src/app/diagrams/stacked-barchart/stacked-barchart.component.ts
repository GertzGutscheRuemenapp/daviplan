import { AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import * as d3 from 'd3';

export interface StackedData {
  year: number,
  values: number[]
}

@Component({
  selector: 'app-stacked-barchart',
  templateUrl: './stacked-barchart.component.html',
  styleUrls: ['./stacked-barchart.component.scss']
})
export class StackedBarchartComponent implements AfterViewInit {

  @Input() data?: StackedData[];
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() labels?: string[];
  @Input() drawLegend: boolean = true;
  @Input() width?: number;
  @Input() height?: number;

  private svg: any;
  private margin: {top: number, bottom: number, left: number, right: number } = {
    top: 50,
    bottom: 30,
    left: 30,
    right: 60
  };

  ngAfterViewInit(): void {
    this.createSvg();
    if (this.data) this.draw(this.data);
  }

  private createSvg(): void {
    let figure = d3.select("figure#stacked-barchart");
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

  private draw(data: StackedData[]): void {
    if (data.length == 0) return

    if (!this.labels)
      this.labels = d3.range(0, data[0].values.length).map(d=>d.toString());
    let colorScale = d3.scaleOrdinal(d3.schemeCategory10);
    let max = d3.max(data, d => { return d.values.reduce((a, c) => a + c) });
    let innerWidth = this.width! - this.margin.left - this.margin.right,
        innerHeight = this.height! - this.margin.top - this.margin.bottom;
    // Add X axis
    const x = d3.scaleBand()
      .range([0, innerWidth])
      .domain(data.map(d => d.year.toString()))
      .padding(0.5);

    this.svg.append("g")
      .attr("transform",`translate(${this.margin.left},${innerHeight + this.margin.top})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end");

    // Add Y axis
    const y = d3.scaleLinear()
      .domain([0, max!])
      .range([innerHeight, 0]);

    this.svg.append("g")
      .attr("transform", `translate(${this.margin.left},${this.margin.top})`)
      .call(d3.axisLeft(y));

    // Create and fill the bars
    this.svg.selectAll("stacks")
    .data(data)
    .enter().append("g")
      // .attr("x", (d: StackedData) => x(d.year.toString()))
      .attr("transform", (d: StackedData) => `translate(${x(d.year.toString())! + this.margin.left}, ${this.margin.top})`)
      .selectAll("rect")
      .data((d: StackedData) => {
        // stack by summing up every element with its predecessors
        let stacked = d.values.map((v, i) => d.values.slice(0, i+1).reduce((a, b) => a + b));
        // draw highest bars first
        return stacked.reverse();
      })
      .enter().append("rect")
        .attr("fill", (d: number, i: number) => colorScale(i.toString()))
        .attr("y", (d: number) => y(d) )
        .attr("width", x.bandwidth())
        .attr("height", (d: number) => innerHeight - y(d));

    let size = 15;
    if (this.drawLegend) {

      this.svg.selectAll("legendRect")
        .data(this.labels.reverse())
        .enter()
        .append("rect")
        .attr("x", innerWidth + this.margin.left)
        .attr("y", (d: string, i: number) => 100 + (i * (size + 5))) // 100 is where the first dot appears. 25 is the distance between dots
        .attr("width", size)
        .attr("height", size)
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
