import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'arrayFilter',
  pure: false
})
export class ArrayFilterPipe implements PipeTransform {
  transform(items: any[], field : string, value : string | boolean | number): any {
    return items.filter(item => item[field] === value);
  }
}
