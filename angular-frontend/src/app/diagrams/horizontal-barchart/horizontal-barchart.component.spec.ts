import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HorizontalBarchartComponent } from './horizontal-barchart.component';

describe('VerticalBarchartComponent', () => {
  let component: HorizontalBarchartComponent;
  let fixture: ComponentFixture<HorizontalBarchartComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ HorizontalBarchartComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HorizontalBarchartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
