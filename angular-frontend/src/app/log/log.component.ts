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
  private wsURL = `${ environment.apiPath }/ws/log/`;
  private chatSocket: WebSocket;

  entries: LogEntry[] = [];

  constructor() {
    this.wsURL = this.wsURL.replace('http:', environment.production? 'wss:': 'ws');
    this.chatSocket = new WebSocket(`${ this.wsURL }${ this.room }`);
    this.chatSocket.onmessage = function (e) {
      console.log(e);
    }
  }

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
