import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgeTreeComponent } from './age-tree.component';

describe('AgeTreeComponent', () => {
  let component: AgeTreeComponent;
  let fixture: ComponentFixture<AgeTreeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AgeTreeComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AgeTreeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
