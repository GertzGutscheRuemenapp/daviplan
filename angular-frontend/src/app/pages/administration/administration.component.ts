import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-administration',
  templateUrl: './administration.component.html',
  styleUrls: ['./administration.component.scss']
})

export class AdministrationComponent implements OnInit {

  menuItems = [
    {name:  $localize`Grundeinstellungen`, url: 'admin/einstellungen', children: []},
    {name:  $localize`Projektgebiet`, url: 'admin/projektgebiet', children: []},
    {name:  $localize`Infrastrukturbereiche`, url: 'admin/infrastruktur', children: []},
    {name:  $localize`Personen und Berechtigungen`, url: 'admin/benutzer', children: []},
    {name:  $localize`Koordination der Grundlagendaten`, url: 'admin/koordination', children: []}
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
