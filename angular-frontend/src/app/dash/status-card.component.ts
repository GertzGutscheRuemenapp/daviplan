// card.component.ts
import {  Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-status-card',
  templateUrl: './status-card.component.html',
  styleUrls: [ './status-card.component.scss']
})

export class StatusCardComponent implements OnInit {
  @Input() title!: string;
  @Input() infoText: string = '';
  @Input() width: string = '';
  @Input() showSpinner: boolean = true;


  constructor () {}
  ngOnInit() {
  }
}
