import { Component, Input } from '@angular/core';
import * as d3 from "d3";
import { v4 as uuid } from "uuid";
import { saveSvgAsPng } from "save-svg-as-png";

@Component({
  selector: 'app-diagram',
  templateUrl: './diagram.component.html',
  styleUrls: ['./diagram.component.scss']
})
export class DiagramComponent {
  @Input() figureId: String = `figure-${uuid()}`;
  @Input() width?: number;
  @Input() height?: number;
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() showPNGExport: boolean = false;
  @Input() showCSVExport: boolean = false;

  protected svg: any;

  constructor() { }

  draw(data: any): void { }

  protected createSvg(): void {
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
    this.svg.append("style").text('text {font-family: sans-serif}')
  }

  clear(): void {
    this.svg.selectAll('*').remove();
  }

  downloadPNG(): void {
    saveSvgAsPng(this.svg.node(), `${this.title || 'Diagramm'}${this.subtitle? ' - ' + this.subtitle: ''}.png`,
      { backgroundColor: 'white' });
  }
  getCSVRows(): (string | number)[][] {
    return [];
  }

  downloadCSV(): void {
    // UTF-8 BOM
    let csvContent = 'data:text/csv;charset=utf-8,\uFEFF';
    const rows = this.getCSVRows();
    rows.forEach(row => {
      const rTxt = row.map(d => (typeof d === 'number')? d.toLocaleString(): d).join(';');
      csvContent += rTxt + "\r\n";
    });
    const link = document.createElement('a');
    link.setAttribute('href', encodeURI(csvContent));
    link.setAttribute('download', `${this.title || 'Diagramm'}${this.subtitle? ' - ' + this.subtitle: ''}.csv`);
    document.body.appendChild(link);
    link.click();
  }
}
