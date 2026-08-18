import {
  AfterViewChecked,
  Component,
  ElementRef,
  input,
  viewChild,
} from '@angular/core';

import { Message } from '../../../models/message.model';
import { MessageBubble } from '../message-bubble/message-bubble';

@Component({
  selector: 'app-message-list',
  standalone: true,
  imports: [MessageBubble],
  templateUrl: './message-list.html',
  styleUrl: './message-list.css',
})
export class MessageList implements AfterViewChecked {
  readonly messages = input.required<Message[]>();

  readonly isTyping = input<boolean>(false);

  private readonly scrollContainer = viewChild.required<ElementRef<HTMLElement>>('scroll');

  ngAfterViewChecked(): void {
    const container = this.scrollContainer().nativeElement;
    container.scrollTop = container.scrollHeight;
  }
}
