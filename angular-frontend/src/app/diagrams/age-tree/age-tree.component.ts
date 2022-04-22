import { AfterViewInit, Component, Input, ViewEncapsulation } from '@angular/core';
import * as d3 from "d3";

export interface AgeTreeData {
  group: string,
  female: number,
  male: number
}

function translation(x: number, y: number) {
  return 'translate(' + x + ',' + y + ')';
}

@Component({
  encapsulation: ViewEncapsulation.None,
  selector: 'app-age-tree',
  templateUrl: './age-tree.component.html',
  styleUrls: ['./age-tree.component.scss']
})
export class AgeTreeComponent implements AfterViewInit {
  @Input() data?: AgeTreeData[];
  @Input() figureId: String = 'age-tree';
  @Input() width: number = 0;
  @Input() height: number = 0;
  @Input() title: string = '';
  @Input() subtitle: string = '';

  private svg: any;
  public margin: { top: number, bottom: number, left: number, right: number, middle: number } = {
    top: 40,
    right: 20,
    bottom: 40,
    left: 20,
    middle: 10
  };

  ngAfterViewInit(): void {
    this.createSvg();
    if (this.data) this.draw(this.data);
  }

  private createSvg(): void {
    let figure = d3.select(`figure#${this.figureId}`);
    if (!(this.width && this.height)) {
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

  public draw(data: AgeTreeData[]): void {

    const groups = data.map(d => d.group),
          femaleAges = data.map(d => d.female),
          maleAges = data.map(d => d.male);

    const width = this.width - (this.margin.left + this.margin.right) - 20;
    const height = this.height - (this.margin.top + this.margin.bottom);

    const regionWidth = width / 2 - this.margin.middle;
    const pointA = regionWidth,
          pointB = width - regionWidth;

    // TITLE

    this.svg.append('text')
      .attr('class', 'title')
      .attr('x', 0)
      .attr('y', 10)
      .text(this.title);

    this.svg.append('text')
      .attr('class', 'subtitle')
      .attr('x', 0)
      .attr('y', 10)
      .attr('font-size', '0.8em')
      .attr('dy', '1em')
      .text(this.subtitle);

    const maxX = femaleAges.concat(maleAges).reduce((a, b) => Math.max(a, b));
    const maxY = data.length;

    const xScale = d3.scaleLinear()
      .domain([0, maxX])
      .range([0, regionWidth])
      .nice();

    const yScale = d3.scaleLinear()
      .domain([0, maxY])
      .range([height, 0]);

    // tooltip

    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style("display", 'none');

    function onMouseMove(this: any, event: MouseEvent){
      tooltip.style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - parseInt(tooltip.style('height'))) + 'px');
    }

    const mouseOverBar = function (event: MouseEvent, d: any) {
      // @ts-ignore
      const i = event.currentTarget?.getAttribute('index');
      if (i === undefined) return;
      const leftBar = d3.select(leftBars._groups[0][i]);
      const rightBar = d3.select(rightBars._groups[0][i]);
      leftBar.selectAll('rect').classed('highlight', true);
      rightBar.selectAll('rect').classed('highlight', true);

      let text = `${groups[i]} <br>`;
      text += 'Anzahl weiblich: <b>' + femaleAges[i] + '</b><br>';
      text += 'Anzahl männlich: <b>' + maleAges[i] + '</b><br>';

      tooltip.style("display", null);
      tooltip.html(text);
    };

    const mouseOutBar = function (event: MouseEvent, d: any) {
      leftBars.selectAll('rect').classed('highlight', false);
      rightBars.selectAll('rect').classed('highlight', false);
      tooltip.style("display", 'none');
    };

    const barHeight = height / maxY;

    const maleGroup = this.svg.append('g')
      .attr('class', 'maleGroup')
      .attr('transform', translation(pointA, this.margin.top) + 'scale(-1,1)');

    const femaleGroup = this.svg.append('g')
      .attr('class', 'femaleGroup')
      .attr('transform', translation(pointB, this.margin.top));

    const rightBars = femaleGroup.selectAll('g')
      .data(femaleAges)
      .enter().append('g')
      .attr('transform', function (d: number, i: number) {
        return translation(0, (maxY - i) * barHeight - barHeight / 2);
      });

    // bars

    rightBars.append('rect')
      .attr('class', 'female')
      .attr('width', xScale)
      .attr('height', barHeight - 1)
      .attr('index', function (d: number, i: number) {
        return i;
      })
      .on('mousemove', onMouseMove)
      .on('mouseover', mouseOverBar)
      .on('mouseout', mouseOutBar);

    const leftBars = maleGroup.selectAll('g')
      .data(maleAges)
      .enter().append('g')
      .attr('transform', function (d: number, i: number) {
        return translation(0, (maxY - i) * barHeight - barHeight / 2);
      });

    leftBars.append('rect')
      .attr('class', 'male')
      .attr('width', xScale)
      .attr('height', barHeight - 1)
      .attr('index', function (d: number, i: number) {
        return i;
      })
      .on('mousemove', onMouseMove)
      .on('mouseover', mouseOverBar)
      .on('mouseout', mouseOutBar);

    // axes
    this.svg.append("g")
      .attr('class', 'axis y')
      .attr('transform', translation(width / 2, this.margin.top))
      .call(
        d3.axisRight(yScale)
          .ticks(maxY)
          .tickSize(0)
          .tickPadding(1)
          .tickFormat((d: any) => groups[d])
      )
      .selectAll('text')
      .attr('class', 'shadow')
      .style('text-anchor', 'middle');

    this.svg.append("g")
      .attr('class', 'axis x right')
      .attr('transform', translation(pointB, height + 10 + this.margin.top))
      .call(
        d3.axisBottom(xScale)
          .ticks(5)
          .tickSize(-height)
          .tickFormat(d3.format("d"))
      );

    this.svg.append("g")
      .attr('class', 'axis x left')
      .attr('transform', translation(0, height + 10 + this.margin.top))
      .call(
        d3.axisBottom(xScale.copy().range([pointA, 0]))
          .ticks(5)
          .tickSize(-height)
          .tickFormat(d3.format("d"))
      );


    // legend

    this.svg.append('text')
      .attr('x', (width / 2) + this.margin.left + 2)
      .attr('y', -5)
      .attr('font-weight', 'bold')
      .attr('text-anchor', 'middle')
      .text('Alter');

    this.svg.append('text')
      .attr('class', 'male')
      .attr('text-anchor', 'middle')
      .text('Anzahl männlich')
      .attr('x', width / 4 + this.margin.left)
      .attr('y', height + this.margin.top + this.margin.bottom);

    this.svg.append('text')
      .attr('class', 'female')
      .attr('text-anchor', 'middle')
      .text('Anzahl weiblich')
      .attr('x', 3 * width / 4 + this.margin.left)
      .attr('y', height + this.margin.top + this.margin.bottom);

  }

  public clear(): void {
    this.svg.selectAll("*").remove();
  }

}
