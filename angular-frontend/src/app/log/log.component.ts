import { Component, AfterViewInit, ElementRef, ViewChild, Input, AfterViewChecked } from '@angular/core';
import { environment } from "../../environments/environment";
import { LogEntry } from "../rest-interfaces";

@Component({
  selector: 'app-log',
  templateUrl: './log.component.html',
  styleUrls: ['./log.component.scss']
})
export class LogComponent implements AfterViewInit, AfterViewChecked {
  @Input() height: string = '100%';
  @Input() room: string = '';
  @ViewChild('log') logEl!: ElementRef;
  private wsURL: string;
  private retries = 0;
  private chatSocket?: WebSocket;

  entries: LogEntry[] = [];

  constructor() {
    const host = environment.production? window.location.hostname: environment.backend.replace('http://', '');
    this.wsURL = `${(environment.production && host.indexOf('localhost') === -1)? 'wss:': 'ws:'}//${host}/ws/log/`
  }

  ngAfterViewInit(): void {
    this.entries.map(entry => this.addLogEntry(entry));
    this.connect();
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  connect(): void {
    if (!this.room) return;
    if (this.retries > 10) return;
    this.chatSocket = new WebSocket(`${ this.wsURL }${ this.room }/`);
    this.chatSocket.onopen = e => this.retries = 0;
    this.chatSocket.onmessage = e => {
      this.addLogEntry(JSON.parse(e.data));
    }
    this.chatSocket.onclose = e => {
      this.retries += 1;
      this.connect();
    };
  }

  addLogEntry(entry: LogEntry): void {
    if (entry.timestamp)
      // cut off milliseconds
      entry.timestamp = entry.timestamp.split(',')[0];
    this.entries.push(entry);
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
      this.logEl.nativeElement.scrollTop = this.logEl.nativeElement.scrollHeight;
  }
}
