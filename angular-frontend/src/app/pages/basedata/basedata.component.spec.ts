import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BasedataComponent } from './basedata.component';

describe('BasedataComponent', () => {
  let component: BasedataComponent;
  let fixture: ComponentFixture<BasedataComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BasedataComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BasedataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
