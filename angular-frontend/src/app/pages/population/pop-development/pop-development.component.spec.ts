import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PopDevelopmentComponent } from './pop-development.component';

describe('PopDevelopmentComponent', () => {
  let component: PopDevelopmentComponent;
  let fixture: ComponentFixture<PopDevelopmentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PopDevelopmentComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PopDevelopmentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
