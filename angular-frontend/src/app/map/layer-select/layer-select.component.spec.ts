import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LayerSelectComponent } from './layer-select.component';

describe('LayerSelectComponent', () => {
  let component: LayerSelectComponent;
  let fixture: ComponentFixture<LayerSelectComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ LayerSelectComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LayerSelectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
