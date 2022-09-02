import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-basedata',
  templateUrl: './basedata.component.html',
  styleUrls: ['./basedata.component.scss']
})
export class BasedataComponent implements OnInit {

  menuItems = [
    {name:  $localize`Gebiete`, url: 'grundlagendaten/gebiete', icon: 'public', children: []},
    {name:  $localize`Bevölkerung`, icon: 'groups', url: '', children: [
        {name:  $localize`Realdaten`, url: 'grundlagendaten/realdaten', icon: 'timeline', children: []},
        {name:  $localize`Prognosedaten`, url: 'grundlagendaten/prognosedaten', icon: 'auto_graph', children: []},
        // {name:  $localize`Einwohnerraster`, url: 'grundlagendaten/einwohnerraster', icon: 'grid_4x4', children: []},
        {name:  $localize`Bevölkerungssalden`, url: 'grundlagendaten/statistiken', icon: 'family_restroom', children: []}
      ]
    },
    {name:  $localize`Infrastrukturdaten`, icon: 'business', url: '', children: [
        {name:  $localize`Leistungen`, url: 'grundlagendaten/leistungen', davicon: 'icon-GGR-davicons-Font-Simple-3-Standorte-Leistungen', children: []},
        {name:  $localize`Standorte und Kapazitäten`, url: 'grundlagendaten/standorte', icon: 'place', children: []},
        {name:  $localize`Nachfrageberechnung`, url: 'grundlagendaten/nachfrage', icon: 'reduce_capacity', children: []}
      ]
    },
    {name:  $localize`Erreichbarkeiten`, davicon: 'icon-GGR-davicons-Font-Simple-5-Fortbewegung-Wegezeit', url: '', children: [
        {name:  $localize`Straßennetz`, url: 'grundlagendaten/strassennetz', icon: 'route', children: []},
        {name:  $localize`ÖPNV-Netz`, url: 'grundlagendaten/oepnvnetz', icon: 'directions_bus_filled', children: []}
      ]
    },
    {name:  $localize`Externe Layer`, url: 'grundlagendaten/layer', icon: 'layers', children: []}
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
