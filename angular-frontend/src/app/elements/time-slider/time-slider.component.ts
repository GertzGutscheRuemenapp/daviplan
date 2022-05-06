import { AfterViewInit, Component, EventEmitter, Input, OnInit, Output, Renderer2, ViewChild } from '@angular/core';
import { MatSlider } from "@angular/material/slider";

@Component({
  selector: 'app-time-slider',
  templateUrl: './time-slider.component.html',
  styleUrls: ['./time-slider.component.scss']
})
export class TimeSliderComponent implements AfterViewInit {
  @Input() years: number[] = [];
  @ViewChild('slider') slider!: MatSlider;
  @Input() value?: number = 0;
  @Input() prognosisStart?: number;
  @Input() helpYOffset = -130;
  @Output() onChange: EventEmitter<number> = new EventEmitter();
  overlay: any;

  constructor(private renderer: Renderer2) { }

  ngAfterViewInit(): void {
    if (this.years.length > 0)
      this.draw();
  }

  draw(): void {
    if (this.overlay){
      const sliderEl = this.slider._elementRef.nativeElement;
      this.renderer.removeChild(sliderEl, this.overlay);
    }
    const sliderEl = this.slider._elementRef.nativeElement;
    this.overlay = this.renderer.createElement('div');
    this.renderer.appendChild(sliderEl, this.overlay);
    if (this.prognosisStart)
      this.createDivider();
    this.addTicks();
  }

  createDivider(): void {
    const sliderEl = this.slider._elementRef.nativeElement;
    let range = this.years[this.years.length - 1] - this.years[0];
    let step = (sliderEl.offsetWidth - 16) / range;

    const divider = this.renderer.createElement('div');
    this.renderer.addClass(divider, 'divider');
    const wrapper = this.renderer.createElement('div');
    this.renderer.addClass(wrapper, 'real-data-wrapper');
    const leftLabel = this.renderer.createElement('label');
    this.renderer.addClass(leftLabel, 'divider-label');
    leftLabel.innerHTML = 'Realdaten';
    const rightLabel = this.renderer.createElement('label');
    this.renderer.addClass(rightLabel, 'divider-label');
    rightLabel.innerHTML = 'Prognosedaten';

    this.renderer.appendChild(this.overlay, divider);
    this.renderer.appendChild(this.overlay, wrapper);
    this.renderer.appendChild(this.overlay, leftLabel);
    this.renderer.appendChild(this.overlay, rightLabel);

    const prognosisPos = (this.prognosisStart! - this.years[0]) * step;
    const progIdx = this.years.indexOf(this.prognosisStart!);
    const gap = (this.prognosisStart! - this.years[progIdx - 1]) * step;
    this.renderer.setStyle(divider, 'left', `${prognosisPos + 8 - gap/2}px`);
    this.renderer.setStyle(rightLabel, 'left', `${prognosisPos + 12 - gap/2}px`);
    this.renderer.setStyle(wrapper, 'width', `${prognosisPos + 4 - gap/2}px`);
    this.renderer.setStyle(leftLabel, 'left', `${prognosisPos - leftLabel.offsetWidth + 6 - gap/2}px`);
  }

  addTicks(): void {
    const sliderEl = this.slider._elementRef.nativeElement;
    let range = this.years[this.years.length - 1] - this.years[0];
    let step = (sliderEl.offsetWidth - 16) / range;
    this.years.forEach((year, i ) => {
      let pos = (year - this.years[0]) * step;
      const tick = this.renderer.createElement('div');
      this.renderer.addClass(tick, 'year-tick');
      // this.renderer.setProperty(tick,'title', year);
      this.renderer.setStyle(tick, 'left', `${pos + 6}px`);
      this.renderer.appendChild(this.overlay, tick);

      const label = this.renderer.createElement('label');
      label.innerHTML = year;
      this.renderer.appendChild(tick, label);
    })

  }

  sliderMoved(ev: any){
    let year = ev.value;
    if (this.years.indexOf(year) == -1) {
      let i;
      for (i = 0; i < this.years.length; i++) {
        if (this.years[i] > year)
          break;
      }
      year = this.years[i];
      this.slider.value = year;
    }
    this.value = year;
  }

  inputChanged(ev: any){
    this.onChange.emit(this.value);
  }
}
