import {
  Component,
  AfterViewInit,
  ElementRef,
  ViewChild,
  Input,
  AfterViewChecked,
  OnDestroy,
  Output, EventEmitter, ChangeDetectorRef
} from '@angular/core';
import { environment } from "../../environments/environment";
import { LogEntry } from "../rest-interfaces";
import { RestCacheService } from "../rest-cache.service";

@Component({
  selector: 'app-log',
  templateUrl: './log.component.html',
  styleUrls: ['./log.component.scss']
})
export class LogComponent implements AfterViewInit, AfterViewChecked, OnDestroy {
  @Input() height: string = '200px';
  @Input() room: string | undefined = '';
  @Input() fetchOldLogs: boolean = true;
  @ViewChild('log') logEl!: ElementRef;
  @Output() onMessage = new EventEmitter<LogEntry>();
  readonly wsURL: string;
  private retries = 0;
  private chatSocket?: WebSocket;

  entries: LogEntry[] = [];

  constructor(private restService: RestCacheService, private cdref: ChangeDetectorRef) {
    // in local dev the location equals
    const host = environment.backend? environment.backend.replace('http://', ''): window.location.hostname;
    this.wsURL = `${(environment.production && host.indexOf('localhost') === -1)? 'wss:': 'ws:'}//${host}/ws/log/`;
  }

  ngAfterViewInit(): void {
    if (this.fetchOldLogs)
      this.restService.getLogs({ room: this.room, reset: true, level: environment.loglevel }).subscribe(entries => {
        entries.forEach(entry => this.addLogEntry(entry));
        this.cdref.detectChanges();
        this.scrollToBottom(true);
        this.connect();
      });
    else
      this.connect();
  }

  ngAfterViewChecked() {
    this.scrollToBottom(false);
  }

  connect(): void {
    if (!this.room) return;
    if (this.retries > 10) return;
    this.chatSocket = new WebSocket(`${ this.wsURL }${ this.room }/`);
    this.chatSocket.onopen = e => this.retries = 0;
    this.chatSocket.onmessage = e => {
      const logEntry = JSON.parse(e.data);
      this.addLogEntry(logEntry);
      this.onMessage.emit(logEntry);
    }
    this.chatSocket.onclose = e => {
      this.retries += 1;
      this.connect();
    };
  }

  addLogEntry(entry: LogEntry): void {
    if (!entry.message) return;
    if (environment.loglevel === 'INFO' && entry.level === 'DEBUG') return;
    if (entry.timestamp)
      // cut off milliseconds
      entry.timestamp = entry.timestamp.split(',')[0];
    this.entries.push(entry);
  }

  scrollToBottom(forced= true): void {
    // if not forced: scroll automatically to bottom if already close to bottom, do not if manually scrolled up
    if (forced || Math.abs(this.logEl.nativeElement.scrollHeight - this.logEl.nativeElement.scrollTop) < 500)
      this.logEl.nativeElement.scrollTop = this.logEl.nativeElement.scrollHeight;
  }

  ngOnDestroy(): void {
    this.room = undefined;
    this.chatSocket?.close();
  }
}
