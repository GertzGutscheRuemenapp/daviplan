// card.component.ts
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-dash-card',
  templateUrl: './dash-card.component.html',
  styleUrls: ['./dash-card.component.scss']
})

export class CardComponent{
  @Input() title: string = '';
  @Input() infoText: string = '';
  @Input() height: string = 'auto';

  constructor() {}
}
