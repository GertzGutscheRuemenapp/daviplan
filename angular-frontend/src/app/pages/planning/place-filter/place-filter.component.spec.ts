import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PlaceFilterComponent } from './place-filter.component';

describe('ServiceFilterComponent', () => {
  let component: PlaceFilterComponent;
  let fixture: ComponentFixture<PlaceFilterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PlaceFilterComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PlaceFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
