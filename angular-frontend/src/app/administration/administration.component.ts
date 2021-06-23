import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-administration',
  templateUrl: './administration.component.html',
  styleUrls: ['./administration.component.scss']
})
export class AdministrationComponent implements OnInit {

  menuItems = [
    {name:  $localize`Grundeinstellungen`, url: 'admin/settings'},
    {name:  $localize`Projektgebiet`, url: 'admin/project'},
    {name:  $localize`Infrastrukturbereiche`, url: 'admin/infrastructure'},
    {name:  $localize`Personen und Berechtigungen`, url: 'admin/users'},
    {name:  $localize`Koordination der Grundlagendaten`, url: 'admin/coordination'}
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
