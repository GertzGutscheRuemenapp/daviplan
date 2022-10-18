import { CookieService as NgxCookieService } from "ngx-cookie-service";

import { Injectable } from "@angular/core";

@Injectable({
  providedIn: 'root'
})
export class CookieService {
  constructor(private ngxCookies: NgxCookieService){}

  toggle(name: string, path?: string | undefined) {
    let val = (!this.ngxCookies.check(name) || this.ngxCookies.get(name) === 'false')? 'true': 'false';
    this.ngxCookies.set(name, val, { path: path, expires: 3650 });
  }

  // public get(name: string): string | undefined {
  //   let val = this.ngxCookies.get(name);
  //   return val;
  // }

  public get(name: string): any;
  public get(name: string, type: 'string'): string;
  public get(name: string, type: 'boolean'): boolean | undefined;
  public get(name: string, type: 'number'): number | undefined;
  public get(name: string, type: 'array'): string[];
  public get(name: string, type: 'json'): any;
  public get(name: string, type: string = 'string'): unknown {
    let val = this.ngxCookies.get(name);
    if (type === 'boolean') {
      if (val === undefined || val === '') return;
      if (val.toLocaleLowerCase() === 'false')
        return false;
      return true;
    }
    if (type === 'array'){
      if (!val) return [];
      return val.split(',');
    }
    if (type === 'number'){
      if (val === undefined || val === '') return;
      return Number(val);
    }
    if (type === 'string'){
      return val || '';
    }
    if (type === 'json'){
      return JSON.parse(val) || {};
    }
    return val;
  }

  public set(name: string, val: any, path?: string | undefined) {
    const strVal = (val.toString)? val.toString(): (val instanceof Object)? JSON.stringify(val): String(val);
    this.ngxCookies.set(name, strVal, { path: path, expires: 3650 });
  }

  public has(name: string) {
    return this.ngxCookies.check(name);
  }
}
