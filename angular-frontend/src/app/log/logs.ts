import { User } from "../rest-interfaces";

export interface LogEntry {
  user?: User,
  date: Date,
  text: string
}

export const mockLogs: LogEntry[] = [
  { date: new Date(Date.now()), text: 'Log noch nicht implementiert'}
/*  {
    date: new Date('2021-12-17T14:24:25'),
    text: 'Lorem ipsum dolor sit amet'
  },
  {
    date: new Date('2021-12-17T14:25:14'),
    text: 'consetetur sadipscing elitr'
  },
  {
    date: new Date('2021-12-17T03:26:04'),
    text: 'sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat'
  },
  {
    date: new Date('2021-12-17T14:24:25'),
    text: 'Lorem ipsum dolor sit amet'
  },
  {
    date: new Date('2021-12-17T14:25:14'),
    text: 'consetetur sadipscing elitr'
  },
  {
    date: new Date('2021-12-17T03:26:04'),
    text: 'sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat'
  },
  {
    date: new Date('2021-12-17T14:24:25'),
    text: 'Lorem ipsum dolor sit amet'
  },
  {
    date: new Date('2021-12-17T14:25:14'),
    text: 'consetetur sadipscing elitr'
  },
  {
    date: new Date('2021-12-17T03:26:04'),
    text: 'sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat'
  },
  {
    date: new Date('2021-12-17T14:24:25'),
    text: 'Lorem ipsum dolor sit amet'
  },
  {
    date: new Date('2021-12-17T14:25:14'),
    text: 'consetetur sadipscing elitr'
  },
  {
    date: new Date('2021-12-17T03:26:04'),
    text: 'sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat'
  },
  {
    date: new Date('2021-12-17T14:24:25'),
    text: 'Lorem ipsum dolor sit amet'
  },
  {
    date: new Date('2021-12-17T14:25:14'),
    text: 'consetetur sadipscing elitr'
  },
  {
    date: new Date('2021-12-17T03:26:04'),
    text: 'sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat'
  },
  {
    date: new Date('2021-12-17T14:24:25'),
    text: 'Lorem ipsum dolor sit amet'
  },
  {
    date: new Date('2021-12-17T14:25:14'),
    text: 'consetetur sadipscing elitr'
  },
  {
    date: new Date('2021-12-17T03:26:04'),
    text: 'sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat'
  }*/
]
