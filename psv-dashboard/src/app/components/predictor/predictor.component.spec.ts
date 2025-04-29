import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PredictorComponent } from './predictor.component';

describe('PredictorComponent', () => {
  let component: PredictorComponent;
  let fixture: ComponentFixture<PredictorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PredictorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PredictorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
