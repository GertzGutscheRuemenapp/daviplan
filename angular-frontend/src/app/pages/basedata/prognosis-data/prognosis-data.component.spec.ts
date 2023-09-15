import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PrognosisDataComponent } from './prognosis-data.component';

describe('PrognosisDataComponent', () => {
  let component: PrognosisDataComponent;
  let fixture: ComponentFixture<PrognosisDataComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PrognosisDataComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PrognosisDataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
