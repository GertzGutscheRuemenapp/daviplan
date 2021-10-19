import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-basedata',
  templateUrl: './basedata.component.html',
  styleUrls: ['./basedata.component.scss']
})
export class BasedataComponent implements OnInit {

  menuItems = [
    {name:  $localize`Gebiete`, url: 'grundlagendaten/gebiete', children: []},
    {name:  $localize`Bevölkerung`, url: '', children: [
        {name:  $localize`Einwohnerraster`, url: 'grundlagendaten/einwohnerraster', children: []},
        {name:  $localize`Realdaten`, url: 'grundlagendaten/realdaten', children: []},
        {name:  $localize`Prognosedaten`, url: 'grundlagendaten/prognosedaten', children: []},
        {name:  $localize`Bevölkerungssalden`, url: 'grundlagendaten/statistiken', children: []}
      ]
    },
    {name:  $localize`Infrastrukturdaten`, url: '', children: [
        {name:  $localize`Leistungen`, url: 'grundlagendaten/leistungen', children: []},
      {name:  $localize`Standorte`, url: 'grundlagendaten/standorte', children: []},
      {name:  $localize`Kapazitäten`, url: 'grundlagendaten/kapazitaeten', children: []},
      {name:  $localize`Nachfragequoten`, url: 'grundlagendaten/nachfragequoten', children: []}
      ]
    },
    {name:  $localize`Indikatoren`, url: 'grundlagendaten/indikatoren', children: []},
    {name:  $localize`Erreichbarkeiten`, url: '', children: [
        {name:  $localize`Wegenetz`, url: 'grundlagendaten/wegenetz', children: []},
        {name:  $localize`Erreichbarkeiten`, url: 'grundlagendaten/erreichbarkeiten', children: []}
      ]
    },
    {name:  $localize`Externe Layer`, url: 'grundlagendaten/layer', children: []}
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
