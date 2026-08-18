import { Routes } from '@angular/router';

import { Chat } from './pages/chat/chat';
import { Scheduler } from './pages/scheduler/scheduler';

export const routes: Routes = [
  {
    path: '',
    component: Chat,
  },
  {
    path: 'chats/:id',
    component: Chat,
  },
  {
    path: 'scheduler',
    component: Scheduler,
  },
  {
    path: 'scheduler/:id',
    component: Scheduler,
  },
  {
    path: '**',
    redirectTo: '',
  },
];
