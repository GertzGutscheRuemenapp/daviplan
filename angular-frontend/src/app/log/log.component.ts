import { Component, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { mockLogs, LogEntry } from "./logs";

@Component({
  selector: 'app-log',
  templateUrl: './log.component.html',
  styleUrls: ['./log.component.scss']
})
export class LogComponent implements AfterViewInit {
  @ViewChild('log') logEl!: ElementRef;

  entries: LogEntry[] = [];

  constructor() { }

  ngAfterViewInit(): void {
    this.entries = mockLogs;
    this.entries.map(entry => this.addLogEntry(entry));
  }

  addLogEntry(entry: LogEntry): void {
    let textArea = this.logEl.nativeElement;
    textArea.value += `${entry.date.toLocaleDateString()} - ${entry.text}\r\n`;
  }

}
