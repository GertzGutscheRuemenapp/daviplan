import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExternalLayersComponent } from './external-layers.component';

describe('ExternalLayersComponent', () => {
  let component: ExternalLayersComponent;
  let fixture: ComponentFixture<ExternalLayersComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ExternalLayersComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ExternalLayersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
