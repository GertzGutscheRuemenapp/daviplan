import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioMenuComponent } from './scenario-menu.component';

describe('ScenarioMenuComponent', () => {
  let component: ScenarioMenuComponent;
  let fixture: ComponentFixture<ScenarioMenuComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScenarioMenuComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ScenarioMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
