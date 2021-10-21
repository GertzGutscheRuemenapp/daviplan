import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RouterSettingsComponent } from './router-settings.component';

describe('RouterSettingsComponent', () => {
  let component: RouterSettingsComponent;
  let fixture: ComponentFixture<RouterSettingsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RouterSettingsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RouterSettingsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
