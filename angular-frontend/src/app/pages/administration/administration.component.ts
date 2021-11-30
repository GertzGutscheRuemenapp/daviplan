import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-administration',
  templateUrl: './administration.component.html',
  styleUrls: ['./administration.component.scss']
})

export class AdministrationComponent implements OnInit {

  menuItems = [
    {name:  $localize`Grundeinstellungen`, icon: 'miscellaneous_services', url: 'admin/einstellungen', children: []},
    {name:  $localize`Projektdefinition`, icon: 'hexagon', url: 'admin/projektdefinition', children: []},
    {name:  $localize`Infrastrukturbereiche`, icon: 'business', url: 'admin/infrastruktur', children: []},
    {name:  $localize`Personen und Berechtigungen`, icon: 'manage_accounts', url: 'admin/benutzer', children: []},
    {name:  $localize`Koordination der Grundlagendaten`, icon: 'format_list_bulleted', url: 'admin/koordination', children: []}
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
