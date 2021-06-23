import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-administration',
  templateUrl: './administration.component.html',
  styleUrls: ['./administration.component.scss']
})
export class AdministrationComponent implements OnInit {

  menuItems = [
    {name:  $localize`Grundeinstellungen`, url: 'admin/settings', children: []},
    {name:  $localize`Projektgebiet`, url: 'admin/project', children: []},
    {name:  $localize`Infrastrukturbereiche`, url: 'admin/infrastructure', children: []},
    {name:  $localize`Personen und Berechtigungen`, url: 'admin/users', children: []},
    {name:  $localize`Koordination der Grundlagendaten`, url: 'admin/coordination', children: []}
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
