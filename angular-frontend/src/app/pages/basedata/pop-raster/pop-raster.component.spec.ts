import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PopRasterComponent } from './pop-raster.component';

describe('PopRasterComponent', () => {
  let component: PopRasterComponent;
  let fixture: ComponentFixture<PopRasterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PopRasterComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PopRasterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
