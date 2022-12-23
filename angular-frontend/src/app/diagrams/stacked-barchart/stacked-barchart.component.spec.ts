import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StackedBarchartComponent } from './stacked-barchart.component';

describe('StackedBarchartComponent', () => {
  let component: StackedBarchartComponent;
  let fixture: ComponentFixture<StackedBarchartComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ StackedBarchartComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(StackedBarchartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
