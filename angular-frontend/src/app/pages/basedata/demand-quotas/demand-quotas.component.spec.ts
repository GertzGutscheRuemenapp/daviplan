import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DemandQuotasComponent } from './demand-quotas.component';

describe('DemandQuotasComponent', () => {
  let component: DemandQuotasComponent;
  let fixture: ComponentFixture<DemandQuotasComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DemandQuotasComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DemandQuotasComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
