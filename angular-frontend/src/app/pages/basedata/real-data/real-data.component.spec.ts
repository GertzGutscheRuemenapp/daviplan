import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RealDataComponent } from './real-data.component';

describe('RealDataComponent', () => {
  let component: RealDataComponent;
  let fixture: ComponentFixture<RealDataComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RealDataComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RealDataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
