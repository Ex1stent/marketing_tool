import { Component, output, signal } from '@angular/core';

@Component({
  selector: 'app-excel-upload',
  standalone: true,
  templateUrl: './excel-upload.html',
  styleUrl: './excel-upload.css',
})
export class ExcelUpload {
  readonly uploaded = output<File>();
  readonly uploading = signal(false);
  readonly fileName = signal<string | null>(null);

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.fileName.set(file.name);
    this.uploading.set(true);
    this.uploaded.emit(file);
    input.value = '';
  }


  setUploading(val: boolean): void {
    this.uploading.set(val);
  }
}
