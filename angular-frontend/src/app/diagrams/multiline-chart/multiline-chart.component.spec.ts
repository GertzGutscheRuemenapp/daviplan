import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MultilineChartComponent } from './multiline-chart.component';

describe('MultilineChartComponent', () => {
  let component: MultilineChartComponent;
  let fixture: ComponentFixture<MultilineChartComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MultilineChartComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MultilineChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
