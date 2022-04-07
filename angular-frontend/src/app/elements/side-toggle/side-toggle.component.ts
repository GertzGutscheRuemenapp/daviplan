import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  TemplateRef
} from '@angular/core';

@Component({
  selector: 'app-side-toggle',
  templateUrl: './side-toggle.component.html',
  styleUrls: ['./side-toggle.component.scss']
})
export class SideToggleComponent implements OnInit {

  @Input() icon?: string;
  @Input() content!: TemplateRef<any>;
  @Input('expanded') _str_expanded?: string;
  @Input() direction: string = 'right';
  @Input() name: string = 'Seitenmenü';
  // does the indicator div go the full height of the content or fixed width (if false)
  @Input() fullHeightIndicator: boolean = false;
  _expanded = false;
  closed: EventEmitter<void>;
  /** Event emitted every time the AccordionItem is opened. */
  opened: EventEmitter<void>;

  constructor() {
    this.closed = new EventEmitter();
    this.opened = new EventEmitter();
  }

  ngOnInit(): void {
    this._expanded = this._str_expanded === '' || this._str_expanded === 'true';
  }

  toggle(): void {
    this.expanded = !this.expanded;
  }

  get expanded(): boolean{
    return this._expanded;
  };
  set expanded(expanded: boolean){
    if (expanded) this.open();
    else this.close();
  };

  open(): void {
    this._expanded = true;
    this.opened.emit();
  }
  close(): void {
    this._expanded = false;
    this.closed.emit();
  }

}
