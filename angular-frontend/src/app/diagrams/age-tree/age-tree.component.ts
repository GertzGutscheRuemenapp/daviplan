import { AfterViewInit, Component, Input, ViewEncapsulation } from '@angular/core';
import * as d3 from 'd3';
import { v4 as uuid } from 'uuid';

export interface AgeTreeData {
  label: string,
  fromAge: number,
  toAge?: number,
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
  @Input() figureId: String = `figure${uuid()}`;
  @Input() ageCutoff: number = 90;
  @Input() width: number = 0;
  @Input() height: number = 0;
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() animate?: boolean;

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
    this.svg = figure.append('svg')
      .attr('viewBox', `0 0 ${this.width!} ${this.height!}`)
      .append('g');
  }

  public draw(data: AgeTreeData[]): void {
    this.clear();

    let femaleAges = Array(this.ageCutoff).fill(0),
        labels = Array(this.ageCutoff),
        yAxisLabels = Array(this.ageCutoff),
        maleAges = Array(this.ageCutoff).fill(0),
        femaleWidths = Array(this.ageCutoff).fill(0),
        maleWidths = Array(this.ageCutoff).fill(0),
        barHeights = Array(this.ageCutoff).fill(1);

    data.forEach((d, i) => {
      if (d.fromAge > this.ageCutoff) return;
      const toAge = Math.min(d.toAge || d.fromAge, this.ageCutoff);
      const diff = 1 + toAge - d.fromAge;
      labels[d.fromAge] = d.label;
      yAxisLabels[d.fromAge] = d.fromAge;
      femaleWidths[d.fromAge] = d.female / diff;
      maleWidths[d.fromAge] = d.male / diff;
      barHeights[d.fromAge] = diff;
      femaleAges[d.fromAge] = d.female;
      maleAges[d.fromAge] = d.male;
    })

    yAxisLabels[yAxisLabels.length - 1] = '+';

    const width = this.width - (this.margin.left + this.margin.right) - 20;
    const height = this.height - (this.margin.top + this.margin.bottom);

    const regionWidth = width / 2 - this.margin.middle;
    const pointA = regionWidth,
          pointB = width - regionWidth;

    // const maxX = femaleAges.concat(maleAges).reduce((a, b) => Math.max(a, b));
    // const maxY = data.length;
    const maxX = femaleWidths.concat(maleWidths).reduce((a, b) => Math.max(a, b));
    const maxY = this.ageCutoff;

    const xScale = d3.scaleLinear()
      .domain([0, maxX])
      .range([0, regionWidth])
      .nice();

    const yScale = d3.scaleLinear()
      .domain([0, maxY])
      .range([height, 0]);

    // axes
    this.svg.append('g')
      .attr('class', 'axis y')
      .attr('transform', translation(this.margin.left + width / 2, this.margin.top))
      .call(
        d3.axisRight(yScale)
          .ticks(maxY)
          .tickSize(0)
          .tickPadding(1)
          .tickFormat((d: any, i: number) => yAxisLabels[i])
      )
      .selectAll('text')
      .attr('class', 'shadow')
      .attr('font-size', '0.8em')
      .style('text-anchor', 'middle');

    this.svg.append('g')
      .attr('class', 'axis x right')
      .attr('transform', translation(this.margin.left + pointB, height + 3 + this.margin.top))
      .call(
        d3.axisBottom(xScale)
          .ticks(5)
          .tickSize(-height)
          .tickFormat(d3.format('d'))
      );

    this.svg.append('g')
      .attr('class', 'axis x left')
      .attr('transform', translation(this.margin.left, height + 3 + this.margin.top))
      .call(
        d3.axisBottom(xScale.copy().range([pointA, 0]))
          .ticks(5)
          .tickSize(-height)
          .tickFormat(d3.format('d'))
      );

    // title

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

    // tooltip

    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style('display', 'none');

    function onMouseMove(this: any, event: MouseEvent){
      tooltip.style('left', event.pageX + 20 + 'px')
        .style('top', event.pageY + 10 + 'px');
    }

    const mouseOverBar = function (event: MouseEvent, d: any) {
      // @ts-ignore
      const i = event.currentTarget?.getAttribute('index');
      if (i === undefined) return;
      const leftBar = d3.select(left._groups[0][i]);
      const rightBar = d3.select(right._groups[0][i]);
      leftBar.selectAll('rect').classed('highlight', true);
      rightBar.selectAll('rect').classed('highlight', true);

      let text = `<b>${labels[i]}</b><br>`;
      text += `<span class='female'><b>Anzahl weiblich:</b></span> ${femaleAges[i].toLocaleString()}<br>`;
      text += `<span class='male'><b>Anzahl männlich:</b></span> ${maleAges[i].toLocaleString()}<br>`;

      tooltip.style('display', null);
      tooltip.html(text);
    };

    const mouseOutBar = function (event: MouseEvent, d: any) {
      left.selectAll('rect').classed('highlight', false);
      right.selectAll('rect').classed('highlight', false);
      tooltip.style('display', 'none');
    };

    const barHeight = height / maxY;
    const _this = this;

    const maleGroup = this.svg.append('g')
      .attr('class', 'maleGroup')
      .attr('transform', translation(this.margin.left + pointA, this.margin.top) + 'scale(-1,1)');

    const femaleGroup = this.svg.append('g')
      .attr('class', 'femaleGroup')
      .attr('transform', translation(this.margin.left + pointB, this.margin.top));

    const right = femaleGroup.selectAll('g')
      .data(femaleAges)
      .enter().append('g')
      .attr('transform', function (d: number, i: number) {
        return translation(0, (maxY - i - barHeights[i]) * barHeight - barHeight / 2);
      });

    // bars

    function widthScale(d: number, i: number): number {
      const bh = barHeights[i];
      if (!bh) return 0;
      return xScale(d / bh);
    }

    const rightBars = right.append('rect')
      .attr('class', 'female')
      .attr('width', (d: number, i: number) => {
        if (this.animate) return 0;
        return widthScale(d, i);
      })
      .attr('height', function (d: number, i: number) {
        return barHeight * barHeights[i] - 1;
      })
      .attr('index', function (d: number, i: number) {
        return i;
      })
      .on('mousemove', onMouseMove)
      .on('mouseover', mouseOverBar)
      .on('mouseout', mouseOutBar);

    const left = maleGroup.selectAll('g')
      .data(maleAges)
      .enter().append('g')
      .attr('transform', function (d: number, i: number) {
        return translation(0, (maxY - i - barHeights[i]) * barHeight - barHeight / 2);
      });

    const leftBars = left.append('rect')
      .attr('class', 'male')
      .attr('width', (d: number, i: number) => {
        if (this.animate) return 0;
        return widthScale(d, i);
      })
      .attr('height', function (d: number, i: number) {
        return barHeight * barHeights[i] - 1;
      })
      .attr('index', function (d: number, i: number) {
        return i;
      })
      .on('mousemove', onMouseMove)
      .on('mouseover', mouseOverBar)
      .on('mouseout', mouseOutBar);

    if (this.animate) {
      rightBars.transition()
        .duration(800)
        .attr('width', (d: number, i: number) => {
          return widthScale(d, i) - widthScale(0, i);
        });
      leftBars.transition()
        .duration(800)
        .attr('width', (d: number, i: number) => {
          return widthScale(d, i) - widthScale(0, i);
        });
    }

    // legend

    this.svg.append('text')
      .attr('x', (width / 2) + this.margin.left + 2)
      .attr('y', this.margin.top - 10)
      .attr('font-size', '0.8em')
      // .attr('font-weight', 'bold')
      .attr('text-anchor', 'middle')
      .text('Alter');

    this.svg.append('text')
      .attr('class', 'male')
      .attr('text-anchor', 'middle')
      .text('Anzahl männlich pro Jahrgang')
      .attr('font-size', '0.8em')
      .attr('x', width / 4 + this.margin.left)
      .attr('y', height + this.margin.top + this.margin.bottom);

    this.svg.append('text')
      .attr('class', 'female')
      .attr('text-anchor', 'middle')
      .text('Anzahl weiblich pro Jahrgang')
      .attr('font-size', '0.8em')
      .attr('x', 3 * width / 4 + this.margin.left)
      .attr('y', height + this.margin.top + this.margin.bottom);
  }

  public clear(): void {
    this.svg.selectAll('*').remove();
  }

}
