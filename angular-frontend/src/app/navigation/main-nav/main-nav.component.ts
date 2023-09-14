import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { Observable } from 'rxjs';
import { share } from 'rxjs/operators';
import { AuthService } from "../../auth.service";
import {Router} from "@angular/router";
import { environment } from "../../../environments/environment";
import { SiteSettings } from "../../settings.service";
import { Infrastructure, User } from "../../rest-interfaces";
import { SimpleDialogComponent } from "../../dialogs/simple-dialog/simple-dialog.component";
import { MatDialog } from "@angular/material/dialog";
import { RestCacheService } from "../../rest-cache.service";

@Component({
  selector: 'app-main-nav',
  templateUrl: './main-nav.component.html',
  styleUrls: ['./main-nav.component.scss']
})
export class MainNavComponent implements OnInit{

  user?: User;
  user$?: Observable<User | undefined>;
  backend: string = environment.backend;
  settings?: SiteSettings;
  infrastructures: Infrastructure[] = [];
  @ViewChild('userTemplate') userTemplate?: TemplateRef<any>;

  menuItems: { name: string, url: string }[] = [];

  constructor(private auth: AuthService, private dialog: MatDialog,
              private router: Router, private rest: RestCacheService) { }

  ngOnInit(): void {
    this.auth.settings.siteSettings$.subscribe(settings => {
      this.settings = settings;
    });
    this.user$ = this.auth.getCurrentUser().pipe(share());
    this.user$.subscribe(user => {
      this.user = user;
      this.buildMenu();
    });
  }

  buildMenu(): void {
    if (this.user) {
      this.menuItems = [
        { name: `Bevölkerung`, url: 'bevoelkerung' },
        { name: `Infrastrukturplanung`, url: 'planung' },
      ];
      if (this.settings?.demoMode || this.user.profile.canEditBasedata || this.user.profile.adminAccess || this.user.isSuperuser)
        this.menuItems.push({ name:  `Grundlagendaten`, url: 'grundlagendaten' })
      if (this.settings?.demoMode || this.user.profile.adminAccess || this.user.isSuperuser)
        this.menuItems.push({ name:  `Administration`, url: 'admin' })
    }
  }

  showProfile(): void {
    this.rest.getInfrastructures().subscribe(infrastructures => {
      this.infrastructures = infrastructures;
      this.dialog.open(SimpleDialogComponent, {
        panelClass: 'absolute',
        width: '400px',
        data: {
          title: 'Kontoinformationen',
          template: this.userTemplate,
          showCloseButton: true,
          showConfirmButton: true,
          infoText: !(this.user?.isSuperuser || this.user?.profile.adminAccess)? 'Sie können selbst keine Änderungen an den Kontoeinstellungen vornehmen. Wenden Sie sich dazu bitte an Ihren Administrator.': 'Sie können die Einstellungen für dieses Konto im Administrationsbereich der Webseite vornehmen.'
        }
      });
    });
  }

  getInfrastructure(id: number): Infrastructure | undefined {
    return this.infrastructures.find(infra => infra.id === id);
  }

  logout(): void {
    this.auth.logout();
  }
}
