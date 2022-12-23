import { Component, OnInit } from "@angular/core";
import { environment } from "../../environments/environment";

@Component({
  templateUrl: './about.component.html',
  styleUrls: ['./welcome.component.scss', './about.component.scss']
})
export class AboutComponent implements OnInit {
  backend: string = environment.backend;

  constructor() {}

  ngOnInit(): void { }

}
