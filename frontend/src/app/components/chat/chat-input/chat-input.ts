import { Component, ElementRef, output, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './chat-input.html',
  styleUrl: './chat-input.css',
})
export class ChatInput {
  readonly send = output<{ text: string; file?: File }>();

  protected readonly draft = signal('');
  protected readonly attachedFile = signal<File | null>(null);

  private readonly fileInput = viewChild.required<ElementRef<HTMLInputElement>>('fileInput');

  protected openFilePicker(): void {
    this.fileInput().nativeElement.click();
  }

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.attachedFile.set(file);
    input.value = '';
  }

  protected removeFile(): void {
    this.attachedFile.set(null);
  }

  protected onSubmit(): void {
    const text = this.draft().trim();
    const file = this.attachedFile();
    if (!text && !file) {
      return;
    }
    this.send.emit({ text, file: file ?? undefined });
    this.draft.set('');
    this.attachedFile.set(null);
  }
}
