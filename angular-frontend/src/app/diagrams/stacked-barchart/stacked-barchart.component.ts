import { Component, Input, OnInit } from '@angular/core';
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
export class StackedBarchartComponent implements OnInit {

  @Input() data?: StackedData[];
  @Input() title?: string = '';
  @Input() groups?: string[];

  private svg: any;
  private margin = 50;
  private width = 750 - (this.margin * 2);
  private height = 400 - (this.margin * 2);

  ngOnInit(): void {
    this.createSvg();
    if (this.data) this.draw(this.data);
  }

  private createSvg(): void {
    this.svg = d3.select("figure#stacked-barchart")
      .append("svg")
      .attr("width", this.width + (this.margin * 2))
      .attr("height", this.height + (this.margin * 2))
      .append("g")
      .attr("transform", "translate(" + this.margin + "," + this.margin + ")");
  }

  private draw(data: StackedData[]): void {
    if (data.length == 0) return

    if (!this.groups)
      this.groups = d3.range(0, data[0].values.length).map(d=>d.toString());
    let colorScale = d3.scaleOrdinal(d3.schemeCategory10);
    let max = d3.max(data, d => { return d.values.reduce((a, c) => a + c) })
    // Add X axis
    const x = d3.scaleBand()
      .range([0, this.width])
      .domain(data.map(d => d.year.toString()))
      .padding(0.2);

    this.svg.append("g")
      .attr("transform", "translate(0," + this.height + ")")
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end");

    // Add Y axis
    const y = d3.scaleLinear()
      .domain([0, max!])
      .range([this.height, 0]);

    let allValues = data.map(d=>{
      let o: any = {};
      d.values.forEach((v, i) =>  o[this.groups![i]] = v);
      return o;
    });
    let stackedData = d3.stack().keys(this.groups)(allValues);

    this.svg.append("g")
      .call(d3.axisLeft(y));

    // Create and fill the bars
    this.svg.selectAll("stacks")
    .data(data)
    .enter().append("g")
      // .attr("x", (d: StackedData) => x(d.year.toString()))
      .attr("transform", (d: StackedData) => `translate(${x(d.year.toString())},0)`)
      .selectAll("rect")
      .data((d: StackedData) => {
        // stack by summing up every element with its predecessors
        let stacked = d.values.map((v, i) => d.values.slice(0, i+1).reduce((a, b) => a + b));
        // draw highest bars first
        return stacked.reverse();
      })
      .enter().append("rect")
        .attr("fill", (d: number, i: number) => colorScale(i.toString()))
        .attr("y", (d: number) => y(d))
        .attr("width", x.bandwidth())
        .attr("height", (d: number) => this.height - y(d));

  }
}
