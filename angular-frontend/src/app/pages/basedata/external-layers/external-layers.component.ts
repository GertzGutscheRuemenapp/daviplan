import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-external-layers',
  templateUrl: './external-layers.component.html',
  styleUrls: ['./external-layers.component.scss']
})
export class ExternalLayersComponent implements OnInit {
  layerGroups = [
    {name: 'Ökologie', children: [{id: 1, name: 'Naturschutzgebiete'}, {id: 2, name: 'Wälder'}, {id: 8, name: 'unzerschnittene Freiräume'}, {id: 8, name: 'Wasserschutzgebiete'}]},
    {name: 'Verkehr', children: [{id: 3, name: 'ÖPNV'}, {id: 4, name: 'Lärmkarte'}, {id: 5, name: 'Fahrradwege'}]},
    {name: 'Infrastruktur', children: [{id: 6, name: 'Hochspannungsmasten'}, {id: 7, name: 'ALKIS Gebäudedaten'}]}
  ]

  constructor() { }

  ngOnInit(): void {
  }

}
