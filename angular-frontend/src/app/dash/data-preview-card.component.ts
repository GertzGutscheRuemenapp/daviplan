// card.component.ts
import { Component, Input, ViewEncapsulation  } from '@angular/core';

@Component({
  selector: 'app-data-card',
  templateUrl: './data-preview-card.component.html',
  styleUrls: ['./data-preview-card.component.scss'],
  encapsulation: ViewEncapsulation.None
})

export class DataPreviewCardComponent{
  @Input() title: string = '';
  @Input() editable: boolean = false;

  constructor() {}
}
