// card.component.ts
import {  Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-status-card',
  templateUrl: './status-card.component.html',
  styleUrls: [ './status-card.component.scss']
})

export class StatusCardComponent implements OnInit {
  @Input() title!: string;
  @Input() infoText: string = '<p>Es laufen gerade Uploads oder Berechnungen in diesem Bereich. Den Fortschritt können Sie der Daten-Historie entnehmen.</p>' +
                              '<p>Während der laufenden Berechnung sind Teile des Bereichs gesperrt. Bitte warten Sie, bis die Berechnungen abgeschlossen sind.</p>';
  @Input() width: string = '';
  @Input() showSpinner: boolean = true;
  @Input() symbol: string = 'lock';

  constructor () {}
  ngOnInit() {
  }
}
