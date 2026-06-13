import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

export default function ImageUploader({ onUpload, multiple = false, label = 'Upload Image' }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onUpload(multiple ? acceptedFiles : acceptedFiles[0]);
    }
  }, [onUpload, multiple]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.bmp'] },
    multiple,
    maxSize: 50 * 1024 * 1024, // 50 MB
  });

  return (
    <div
      {...getRootProps()}
      className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}
      id="image-uploader"
    >
      <input {...getInputProps()} />
      <div className="upload-zone-icon">📁</div>
      <p className="upload-zone-text">
        {isDragActive ? (
          <strong>Drop your image here...</strong>
        ) : (
          <>
            <strong>Click to upload</strong> or drag and drop<br />
            <span className="text-xs text-muted" style={{ marginTop: '8px', display: 'block' }}>
              PNG, JPG, WEBP up to 50MB {multiple ? '• Multiple files' : ''}
            </span>
          </>
        )}
      </p>
    </div>
  );
}
