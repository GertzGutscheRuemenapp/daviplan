import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DemandComponent } from './demand.component';

describe('DemandComponent', () => {
  let component: DemandComponent;
  let fixture: ComponentFixture<DemandComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DemandComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DemandComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
