import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TransitMatrixComponent } from './transit-matrix.component';

describe('ReachabilityMatrixComponent', () => {
  let component: TransitMatrixComponent;
  let fixture: ComponentFixture<TransitMatrixComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TransitMatrixComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TransitMatrixComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
