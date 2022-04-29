import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DemandRateSetViewComponent } from './demand-rate-set-view.component';

describe('DemandQuotaViewComponent', () => {
  let component: DemandRateSetViewComponent;
  let fixture: ComponentFixture<DemandRateSetViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DemandRateSetViewComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DemandRateSetViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
