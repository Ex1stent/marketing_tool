import { Component, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

export interface UploadedFile {
  file: File;
  title: string;
}

@Component({
  selector: 'app-excel-upload',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './excel-upload.html',
  styleUrl: './excel-upload.css',
})
export class ExcelUpload {
  readonly uploaded = output<UploadedFile>();
  readonly uploading = signal(false);
  readonly fileName = signal<string | null>(null);
  readonly showModal = signal(false);
  readonly batchTitle = signal('');

  private selectedFile: File | null = null;

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.fileName.set(file.name);
    this.selectedFile = file;
    this.batchTitle.set(file.name.replace(/\.[^/.]+$/, ''));
    this.showModal.set(true);
    input.value = '';
  }

  confirmUpload(): void {
    if (this.selectedFile) {
      this.showModal.set(false);
      this.uploading.set(true);
      this.uploaded.emit({
        file: this.selectedFile,
        title: this.batchTitle().trim(),
      });
    }
  }

  cancelUpload(): void {
    this.showModal.set(false);
    this.selectedFile = null;
  }

  setUploading(val: boolean): void {
    this.uploading.set(val);
  }
}
