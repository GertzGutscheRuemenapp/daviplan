import { Component, OnInit, ViewChildren, QueryList, ElementRef } from '@angular/core';

@Component({
  selector: 'app-scenario-menu',
  templateUrl: './scenario-menu.component.html',
  styleUrls: ['./scenario-menu.component.scss']
})
export class ScenarioMenuComponent implements OnInit {
  @ViewChildren('scenario') scenarioCards?: QueryList<ElementRef>;
  scenarios: string[] = ['Szenario 1', 'Szenario 2']
  activeScenario: string = 'Status Quo';

  constructor() { }

  ngOnInit(): void {
  }

  toggleScenario(event: Event) {
    if (event.target !== event.currentTarget) return;
    let a = (event.target as Element).attributes;
    this.activeScenario = ((event.target as Element).attributes as any)['data-value'].value;
    this.scenarioCards?.forEach((card: ElementRef) => {
      let el = card.nativeElement;
      if (el.attributes['data-value'].nodeValue === this.activeScenario)
        el.classList.add('active');
      else
        el.classList.remove('active');
    });
  }

}
