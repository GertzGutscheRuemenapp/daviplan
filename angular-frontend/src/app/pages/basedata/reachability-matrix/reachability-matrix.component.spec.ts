import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReachabilityMatrixComponent } from './reachability-matrix.component';

describe('ReachabilityMatrixComponent', () => {
  let component: ReachabilityMatrixComponent;
  let fixture: ComponentFixture<ReachabilityMatrixComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ReachabilityMatrixComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ReachabilityMatrixComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
