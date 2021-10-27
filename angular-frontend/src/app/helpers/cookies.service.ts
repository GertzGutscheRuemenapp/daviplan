import { CookieService as NgxCookieService } from "ngx-cookie-service";

import { Injectable } from "@angular/core";

@Injectable({
  providedIn: 'root'
})
export class CookieService {
  constructor(private ngxCookies: NgxCookieService){}

  toggle(name: string, path?: string | undefined) {
    let val = (!this.ngxCookies.check(name) || this.ngxCookies.get(name) === 'false')? 'true': 'false';
    this.ngxCookies.set(name, val, { path: path });
  }

  public get(name: string): string | boolean {
    let val = this.ngxCookies.get(name);
    if (val === 'false') return false;
    if (val === 'true') return true;
    return val;
  }

  public set(name: string, val: any, path?: string | undefined) {
    this.ngxCookies.set(name, String(val), { path: path });
  }

  public has(name: string) {
    return this.ngxCookies.check(name);
  }
}
