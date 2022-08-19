import { Component, AfterViewInit, ElementRef, ViewChild, Input } from '@angular/core';
import { mockLogs, LogEntry } from "./logs";
import { environment } from "../../environments/environment";

@Component({
  selector: 'app-log',
  templateUrl: './log.component.html',
  styleUrls: ['./log.component.scss']
})
export class LogComponent implements AfterViewInit {
  @ViewChild('log') logEl!: ElementRef;
  @Input() height: string = '100%';
  @Input() room: string = '';
  private wsURL = `${ environment.backend }/ws/log/`;
  private retries = 0;
  private chatSocket?: WebSocket;

  entries: LogEntry[] = [];

  constructor() {
    this.wsURL = this.wsURL.replace('http:', environment.production? 'wss:': 'ws:');
  }

  ngAfterViewInit(): void {
    this.entries = mockLogs;
    this.entries.map(entry => this.addLogEntry(entry));

    this.connect();
  }

  connect(): void {
    if (this.retries > 10) return;
    this.chatSocket = new WebSocket(`${ this.wsURL }${ this.room }/`);
    this.chatSocket.onopen = e => this.retries = 0;
    this.chatSocket.onmessage = e => {
      console.log(e);
      return false;
    }
    this.chatSocket.onclose = e => {
      this.retries += 1;
      this.connect();
    };
  }

  addLogEntry(entry: LogEntry): void {
    let textArea = this.logEl.nativeElement;
    let row = `${entry.date.toLocaleDateString()} ${entry.date.toLocaleTimeString()} - ${entry.text}\r\n`;
    textArea.value += row;
  }

}
