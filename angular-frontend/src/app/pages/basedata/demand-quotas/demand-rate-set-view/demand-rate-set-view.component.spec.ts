import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DemandQuotaViewComponent } from './demand-quota-view.component';

describe('DemandQuotaViewComponent', () => {
  let component: DemandQuotaViewComponent;
  let fixture: ComponentFixture<DemandQuotaViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DemandQuotaViewComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DemandQuotaViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
