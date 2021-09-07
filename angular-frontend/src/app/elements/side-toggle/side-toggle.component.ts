import { Component, Input, OnInit, TemplateRef } from '@angular/core';

@Component({
  selector: 'app-side-toggle',
  templateUrl: './side-toggle.component.html',
  styleUrls: ['./side-toggle.component.scss']
})
export class SideToggleComponent implements OnInit {

  @Input() icon?: string;
  @Input() content!: TemplateRef<any>;
  @Input() expanded: boolean = false;
  @Input() direction: string = 'right';

  constructor() { }

  ngOnInit(): void {
  }


}
