import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SideToggleComponent } from './side-toggle.component';

describe('SideToggleComponent', () => {
  let component: SideToggleComponent;
  let fixture: ComponentFixture<SideToggleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SideToggleComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SideToggleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
