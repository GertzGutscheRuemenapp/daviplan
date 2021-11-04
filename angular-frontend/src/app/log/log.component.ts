import { Component, AfterViewInit, ElementRef, ViewChild, Input } from '@angular/core';
import { mockLogs, LogEntry } from "./logs";

@Component({
  selector: 'app-log',
  templateUrl: './log.component.html',
  styleUrls: ['./log.component.scss']
})
export class LogComponent implements AfterViewInit {
  @ViewChild('log') logEl!: ElementRef;
  @Input() height: string = '100%';

  entries: LogEntry[] = [];

  constructor() { }

  ngAfterViewInit(): void {
    this.entries = mockLogs;
    this.entries.map(entry => this.addLogEntry(entry));
  }

  addLogEntry(entry: LogEntry): void {
    let textArea = this.logEl.nativeElement;
    let row = `${entry.date.toLocaleDateString()} ${entry.date.toLocaleTimeString()} - ${entry.text}\r\n`;
    textArea.value += row;
  }

}
