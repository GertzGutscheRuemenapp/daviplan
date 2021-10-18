import { Component, OnInit } from '@angular/core';
import { User, mockUsers } from "../../login/users";

interface DataDomain {
  name: string, url: string, users: User[], status: {text: String, detail: String}
}

const data: { [name: string]: DataDomain[] } = {
  'geodaten' : [
    { name: 'Gebietseinheit', url: '/grundlagendaten/gebiete', users: [mockUsers[0]], status: { text: '3 Ebenen definiert', detail:'' }},
    { name: 'Einwohnerraster', url: '/grundlagendaten/einwohnerraster', users: [mockUsers[0]], status: { text: 'Zensus 2011', detail:'' }},
    { name: 'Regionalstatistik', url: '/grundlagendaten/statistiken', users: [], status: { text: 'Importiert', detail:'' }},
    { name: 'Externe Layer', url: '/grundlagendaten/layer', users: mockUsers, status: { text: '3 Layer definiert', detail:'' }}
  ],
  'einwohnerdaten' : [
    { name: 'Realdaten', url: '/grundlagendaten/realdaten', users: [mockUsers[1]], status: { text: '5 Jahre definiert', detail:'' }},
    { name: 'Prognosedaten', url: '/grundlagendaten/prognosedaten', users: [mockUsers[1]], status: { text: '-', detail:'' }}
  ]
}

@Component({
  selector: 'app-coordination',
  templateUrl: './coordination.component.html',
  styleUrls: ['./coordination.component.scss']
})
export class CoordinationComponent implements OnInit {
  domains = data;
  Object = Object;

  constructor() { }

  ngOnInit(): void {
  }

}
