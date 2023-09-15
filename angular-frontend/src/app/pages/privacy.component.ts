import { Component, OnInit } from "@angular/core";
import { environment } from "../../environments/environment";

@Component({
  templateUrl: './privacy.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class PrivacyComponent implements OnInit {
  backend: string = environment.backend;

  constructor() {}

  ngOnInit(): void { }

}
