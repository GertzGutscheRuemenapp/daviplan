import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReachabilitiesComponent } from './reachabilities.component';

describe('ReachabilitiesComponent', () => {
  let component: ReachabilitiesComponent;
  let fixture: ComponentFixture<ReachabilitiesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ReachabilitiesComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ReachabilitiesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
