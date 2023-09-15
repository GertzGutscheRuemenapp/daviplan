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
    switch (type) {
      case 'boolean':
        if (val === undefined || val === '') return;
        if (val.toLocaleLowerCase() === 'false')
          return false;
        return true;
      case 'array':
        if (!val) return [];
        return val.split(',');
      case 'number':
        if (val === undefined || val === '') return;
        return Number(val);
      case 'string':
        return val || '';
      case 'json':
        try {
          val = JSON.parse(val);
        }
        catch {
          return;
        }
        return val;
      default:
        return val;
    }
  }

  public set(name: string, val: any, options?: { path?: string | undefined, type?: 'string' | 'boolean' | 'json' | 'array' | 'number'}) {
    let serialVal;
    switch (options?.type) {
      case 'boolean': case 'array': case 'number':
        serialVal = val.toString();
        break;
      case 'string':
        serialVal = val;
        break;
      case 'json':
        serialVal = JSON.stringify(val);
        break;
      default:
        // try to stringify the value
        serialVal = (val !== undefined && val.toString)? val.toString(): (val instanceof Object)? JSON.stringify(val): String(val);
    }
    this.ngxCookies.set(name, serialVal, { path: options?.path, expires: 3650 });
  }

  public has(name: string) {
    return this.ngxCookies.check(name);
  }
}
