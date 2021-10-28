import { Component, Input, OnInit, TemplateRef } from '@angular/core';

@Component({
  selector: 'app-side-toggle',
  templateUrl: './side-toggle.component.html',
  styleUrls: ['./side-toggle.component.scss']
})
export class SideToggleComponent implements OnInit {

  @Input() icon?: string;
  @Input() content!: TemplateRef<any>;
  @Input('expanded') _expanded?: string;
  @Input() direction: string = 'right';
  @Input() name: string = 'Seitenmenü';
  // does the indicator div go the full height of the content or fixed width (if false)
  @Input() fullHeightIndicator: boolean = false;
  expanded = false;

  constructor() { }

  ngOnInit(): void {
    this.expanded = this._expanded === '' || this._expanded === 'true';
  }

}
