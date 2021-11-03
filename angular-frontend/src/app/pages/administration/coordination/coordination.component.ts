import { Component, OnInit } from '@angular/core';
import { User, mockUsers } from "../../login/users";

interface DataDomain {
  name: string,
  url: string,
  users: User[],
  status: { text: string, detail: string },
  marker?: number
}

const data: { [name: string]: DataDomain[] } = {
  'geodaten' : [
    { name: 'Gebietseinheit', url: '/grundlagendaten/gebiete/', users: [mockUsers[0]], status: { text: '3 Ebenen definiert', detail:'' }, marker: 1 },
    { name: 'Einwohnerraster', url: '/grundlagendaten/einwohnerraster/', users: [mockUsers[0]], status: { text: 'Zensus 2011', detail:'' }},
    { name: 'Bevölkerungssalden', url: '/grundlagendaten/statistiken/', users: [], status: { text: 'Importiert', detail:'' }, marker: 1 },
    { name: 'Externe Layer', url: '/grundlagendaten/layer/', users: mockUsers, status: { text: '3 Layer definiert', detail:'' }}
  ],
  'einwohnerdaten' : [
    { name: 'Realdaten', url: '/grundlagendaten/realdaten/', users: [mockUsers[1]], status: { text: '5 Jahre definiert', detail:'' }, marker: 2},
    { name: 'Prognosedaten', url: '/grundlagendaten/prognosedaten/', users: [mockUsers[1]], status: { text: '-', detail:'' }, marker: 3}
  ],
  'erreichbarkeit' : [
    { name: 'Verkehrsnetz', url: '/grundlagendaten/verkehrsnetz/', users: [mockUsers[0]], status: { text: '-', detail:'' }},
    { name: 'Zu Fuß', url: '/grundlagendaten/erreichbarkeiten/', users: [mockUsers[0]], status: { text: '-', detail:'' }},
    { name: 'Rad', url: '/grundlagendaten/erreichbarkeiten/', users: [mockUsers[0]], status: { text: '-', detail:'' }},
    { name: 'Auto', url: '/grundlagendaten/erreichbarkeiten/', users: [mockUsers[0]], status: { text: '-', detail:'' }},
    { name: 'ÖPNV', url: '/grundlagendaten/erreichbarkeiten/', users: [mockUsers[1]], status: { text: '-', detail:'' }},
  ],
  'Infrastruktur' : [
    { name: 'Schulen', url: '/grundlagendaten/standorte/', users: [mockUsers[1]], status: { text: '25 Standorte, 2 Leistungen definiert', detail:'' }, marker: 2},
    { name: 'Kinderbetreuung', url: '/grundlagendaten/standorte/', users: [mockUsers[1]], status: { text: '30 Standorte, 3 Leistungen definiert', detail:'' }, marker: 2},
    { name: 'Ärzte', url: '/grundlagendaten/standorte/', users: [mockUsers[1]], status: { text: '-', detail:'' }},
    { name: 'Feuerwehr', url: '/grundlagendaten/standorte/', users: [mockUsers[1]], status: { text: '-', detail:'' }}
  ],
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
