import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PopStatisticsComponent } from './pop-statistics.component';

describe('PopStatisticsComponent', () => {
  let component: PopStatisticsComponent;
  let fixture: ComponentFixture<PopStatisticsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PopStatisticsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PopStatisticsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
