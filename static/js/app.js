import { FFmpeg } from '/static/vendor/ffmpeg/ffmpeg/index.js';
import { fetchFile, toBlobURL } from '/static/vendor/ffmpeg/util/index.js';

const IMAGE_EXTENSIONS = new Set(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']);
const VIDEO_EXTENSIONS = new Set(['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']);
const AUDIO_EXTENSIONS = new Set(['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']);

const SUPPORTED_FORMATS = {
    image: ['jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff'],
    video: ['mp4', 'avi', 'mov', 'mkv', 'webm', 'gif'],
    audio: ['mp3', 'wav', 'flac', 'aac', 'ogg']
};

const MIME_TYPES = {
    jpeg: 'image/jpeg',
    jpg: 'image/jpeg',
    png: 'image/png',
    webp: 'image/webp',
    gif: 'image/gif',
    bmp: 'image/bmp',
    tiff: 'image/tiff',
    mp4: 'video/mp4',
    avi: 'video/x-msvideo',
    mov: 'video/quicktime',
    mkv: 'video/x-matroska',
    webm: 'video/webm',
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    flac: 'audio/flac',
    aac: 'audio/aac',
    ogg: 'audio/ogg'
};

class MediaForge {
    constructor() {
        this.currentFile = null;
        this.fileType = null;
        this.downloadUrl = null;
        this.downloadFilename = null;
        this.ffmpeg = null;
        this.ffmpegLoaded = false;
        this.isConverting = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // ファイル選択
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));

        // 変換ボタン
        document.getElementById('convert-btn').addEventListener('click', () => this.startConversion());

        // ダウンロードボタン
        document.getElementById('download-btn').addEventListener('click', () => this.downloadFile());

        // 新しいファイルを変換ボタン
        document.getElementById('new-file-btn').addEventListener('click', () => this.reset());

        // 出力形式変更時の処理
        document.getElementById('output-format').addEventListener('change', (e) => {
            this.toggleImageOptions(e.target.value);
        });

        // ヘルプモーダル
        const helpBtn = document.getElementById('help-btn');
        const helpModal = document.getElementById('help-modal');
        const closeModalBtn = document.getElementById('close-modal-btn');

        helpBtn.addEventListener('click', () => this.openHelpModal());
        closeModalBtn.addEventListener('click', () => this.closeHelpModal());

        // モーダル外クリックで閉じる
        helpModal.addEventListener('click', (e) => {
            if (e.target === helpModal) {
                this.closeHelpModal();
            }
        });

        // ESCキーで閉じる
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !helpModal.classList.contains('hidden')) {
                this.closeHelpModal();
            }
        });
    }

    openHelpModal() {
        const modal = document.getElementById('help-modal');
        const modalContent = modal.querySelector('.paper-card');

        modal.classList.remove('hidden');
        // 少し遅らせてアニメーションクラスを適用
        setTimeout(() => {
            modal.classList.remove('opacity-0');
            modalContent.classList.remove('scale-95', 'opacity-0');
            modalContent.classList.add('scale-100', 'opacity-100');
        }, 10);
    }

    closeHelpModal() {
        const modal = document.getElementById('help-modal');
        const modalContent = modal.querySelector('.paper-card');

        modal.classList.add('opacity-0');
        modalContent.classList.remove('scale-100', 'opacity-100');
        modalContent.classList.add('scale-95', 'opacity-0');

        // アニメーション完了後にhiddenを追加
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('drop-zone');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
        });

        dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFileSelect(files[0]);
        }
    }

    async handleFileSelect(file) {
        if (!file) return;

        const fileType = this.getFileType(file.name);
        if (!fileType) {
            this.showError('サポートされていないファイル形式です');
            return;
        }

        this.currentFile = file;
        this.fileType = fileType;

        // ファイル情報を表示
        this.showFileInfo({
            filename: file.name,
            size: file.size,
            file_type: fileType
        });

        // サポート形式を取得
        this.loadSupportedFormats(fileType);
    }

    getFileType(filename) {
        const ext = this.getExtension(filename);
        if (IMAGE_EXTENSIONS.has(ext)) {
            return 'image';
        }
        if (VIDEO_EXTENSIONS.has(ext)) {
            return 'video';
        }
        if (AUDIO_EXTENSIONS.has(ext)) {
            return 'audio';
        }
        return null;
    }

    getExtension(filename) {
        const dotIndex = filename.lastIndexOf('.');
        if (dotIndex === -1) {
            return '';
        }
        return filename.slice(dotIndex).toLowerCase();
    }

    showFileInfo(fileInfo) {
        const uploadSection = document.getElementById('upload-section');
        const fileInfoSection = document.getElementById('file-info');
        const fileDetails = document.getElementById('file-details');

        // アップロードエリアを非表示
        uploadSection.classList.add('hidden');

        // ファイル情報を表示
        const fileSize = this.formatFileSize(fileInfo.size);
        const fileIcon = this.getFileIcon(fileInfo.file_type);

        fileDetails.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="${fileIcon} text-2xl"></i>
                <div>
                    <p class="font-medium text-gray-800">${fileInfo.filename}</p>
                    <p class="text-sm text-gray-500">${fileSize} ? ${fileInfo.file_type.toUpperCase()}</p>
                </div>
            </div>
        `;

        fileInfoSection.classList.remove('hidden');
        fileInfoSection.classList.add('fade-in');
    }

    loadSupportedFormats(fileType) {
        const formats = SUPPORTED_FORMATS[fileType] || [];
        const formatSelect = document.getElementById('output-format');
        formatSelect.innerHTML = '<option value="">選択してください</option>';

        formats.forEach(format => {
            const option = document.createElement('option');
            option.value = format;
            option.textContent = format.toUpperCase();
            formatSelect.appendChild(option);
        });
    }

    toggleImageOptions(format) {
        const imageOptions = document.getElementById('image-options');
        const imageFormats = ['jpeg', 'jpg', 'png', 'webp', 'gif', 'bmp', 'tiff'];

        if (imageFormats.includes(format.toLowerCase())) {
            imageOptions.classList.remove('hidden');
        } else {
            imageOptions.classList.add('hidden');
        }
    }

    async ensureFFmpegLoaded() {
        if (this.ffmpegLoaded) {
            return;
        }

        this.showProgress('変換エンジンを準備中...', 5);
        this.ffmpeg = new FFmpeg();

        this.ffmpeg.on('progress', ({ progress }) => {
            if (!this.isConverting) {
                return;
            }
            const percentage = Math.min(99, Math.round(progress * 100));
            this.updateProgress(Math.max(10, percentage));
        });

        try {
            const baseURL = '/static/vendor/ffmpeg/core';
            const coreURL = await toBlobURL(`${baseURL}/ffmpeg-core.js`, 'text/javascript');
            const wasmURL = await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, 'application/wasm');

            await this.ffmpeg.load({ coreURL, wasmURL });
        } catch (error) {
            console.error('FFmpegの読み込みに失敗しました', error);
            throw new Error('変換エンジンの読み込みに失敗しました。ネットワーク制限やCDNブロックを確認してください。');
        }
        this.ffmpegLoaded = true;
    }

    buildFilenames(file, outputFormat) {
        const ext = this.getExtension(file.name);
        const baseName = file.name.replace(/\.[^/.]+$/, '');
        const downloadName = `${baseName}_converted.${outputFormat}`;
        const inputName = `input${ext}`;
        const outputName = `output.${outputFormat}`;

        return { inputName, outputName, downloadName };
    }

    buildFfmpegArgs({ inputName, outputName, outputFormat, quality, width, height, fileType }) {
        const args = ['-y', '-i', inputName];

        if (fileType === 'image') {
            if (width || height) {
                const scaleWidth = width || -1;
                const scaleHeight = height || -1;
                args.push('-vf', `scale=${scaleWidth}:${scaleHeight}`);
            }

            if (['jpeg', 'jpg', 'webp'].includes(outputFormat)) {
                const qualityMap = { high: '2', medium: '5', low: '10' };
                args.push('-q:v', qualityMap[quality] || '5');
            }
        }

        if (fileType === 'video') {
            if (outputFormat === 'gif') {
                return ['-y', '-i', inputName, '-vf', 'fps=15,scale=480:-1:flags=lanczos', outputName];
            }
            const videoBitrate = { high: '2000k', medium: '1000k', low: '500k' };
            const audioBitrate = { high: '192k', medium: '128k', low: '96k' };
            args.push('-b:v', videoBitrate[quality] || '1000k');
            args.push('-b:a', audioBitrate[quality] || '128k');
        }

        if (fileType === 'audio') {
            const audioBitrate = { high: '320k', medium: '192k', low: '128k' };
            args.push('-b:a', audioBitrate[quality] || '192k');
        }

        args.push(outputName);
        return args;
    }

    async safeDelete(filename) {
        try {
            if (this.ffmpeg?.deleteFile) {
                await this.ffmpeg.deleteFile(filename);
                return;
            }
            if (this.ffmpeg?.FS) {
                this.ffmpeg.FS('unlink', filename);
            }
        } catch (error) {
            // 失敗しても致命的ではないため無視
        }
    }

    getMimeType(format) {
        return MIME_TYPES[format] || 'application/octet-stream';
    }

    canUseCanvasForImage(format) {
        const canvasFormats = new Set(['jpeg', 'jpg', 'png', 'webp']);
        return canvasFormats.has(format.toLowerCase());
    }

    async convertImageWithCanvas(outputFormat, quality, width, height) {
        const qualityMap = { high: 0.95, medium: 0.75, low: 0.5 };
        const mimeType = this.getMimeType(outputFormat);
        const bitmap = await createImageBitmap(this.currentFile);
        let targetWidth = width || bitmap.width;
        let targetHeight = height || bitmap.height;

        if (width && !height) {
            targetHeight = Math.round(bitmap.height * (width / bitmap.width));
        }
        if (height && !width) {
            targetWidth = Math.round(bitmap.width * (height / bitmap.height));
        }

        const canvas = document.createElement('canvas');
        canvas.width = targetWidth;
        canvas.height = targetHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(bitmap, 0, 0, targetWidth, targetHeight);

        const blob = await new Promise((resolve, reject) => {
            const q = ['jpeg', 'jpg', 'webp'].includes(outputFormat) ? (qualityMap[quality] || 0.75) : undefined;
            canvas.toBlob((result) => {
                if (!result) {
                    reject(new Error('画像の変換に失敗しました'));
                    return;
                }
                resolve(result);
            }, mimeType, q);
        });

        bitmap.close();
        return blob;
    }

    async startConversion() {
        const outputFormat = document.getElementById('output-format').value;
        const quality = document.getElementById('quality').value;
        const widthValue = document.getElementById('width').value;
        const heightValue = document.getElementById('height').value;

        if (!outputFormat) {
            this.showError('出力形式を選択してください');
            return;
        }

        if (!this.currentFile) {
            this.showError('ファイルが選択されていません');
            return;
        }

        try {
            const width = widthValue ? Number(widthValue) : null;
            const height = heightValue ? Number(heightValue) : null;

            if (this.fileType === 'image' && this.canUseCanvasForImage(outputFormat)) {
                this.isConverting = true;
                this.showProgress('変換中...', 20);
                document.getElementById('file-info').classList.add('hidden');

                const blob = await this.convertImageWithCanvas(outputFormat, quality, width, height);
                const { downloadName } = this.buildFilenames(this.currentFile, outputFormat);

                if (this.downloadUrl) {
                    URL.revokeObjectURL(this.downloadUrl);
                }

                this.downloadUrl = URL.createObjectURL(blob);
                this.downloadFilename = downloadName;
                this.updateProgress(100);
                this.isConverting = false;

                setTimeout(() => {
                    this.showResult();
                }, 300);
                return;
            }

            await this.ensureFFmpegLoaded();
            this.isConverting = true;
            this.showProgress('変換中...', 10);

            // 変換オプションを非表示
            document.getElementById('file-info').classList.add('hidden');

            const { inputName, outputName, downloadName } = this.buildFilenames(this.currentFile, outputFormat);

            await this.ffmpeg.writeFile(inputName, await fetchFile(this.currentFile));

            const args = this.buildFfmpegArgs({
                inputName,
                outputName,
                outputFormat,
                quality,
                width,
                height,
                fileType: this.fileType
            });

            await this.ffmpeg.exec(args);

            const data = await this.ffmpeg.readFile(outputName);
            const blob = new Blob([data.buffer], { type: this.getMimeType(outputFormat) });

            if (this.downloadUrl) {
                URL.revokeObjectURL(this.downloadUrl);
            }

            this.downloadUrl = URL.createObjectURL(blob);
            this.downloadFilename = downloadName;

            await this.safeDelete(inputName);
            await this.safeDelete(outputName);

            this.updateProgress(100);
            this.isConverting = false;

            setTimeout(() => {
                this.showResult();
            }, 300);

        } catch (error) {
            this.isConverting = false;
            console.error('変換処理でエラーが発生しました', error);
            this.showError(error?.message || '変換に失敗しました');
            this.hideProgress();
            document.getElementById('file-info').classList.remove('hidden');
        }
    }

    showResult() {
        const progressSection = document.getElementById('progress-section');
        const resultSection = document.getElementById('result-section');
        const resultInfo = document.getElementById('result-info');

        progressSection.classList.add('hidden');

        const filenameText = this.downloadFilename ? `保存名: ${this.downloadFilename}` : '';

        resultInfo.innerHTML = `
            <p class="text-gray-700">
                <i class="fas fa-check-circle text-green-600 mr-2"></i>
                ファイルが正常に変換されました
            </p>
            ${filenameText ? `<p class="text-gray-600 mt-2">${filenameText}</p>` : ''}
        `;

        resultSection.classList.remove('hidden');
        resultSection.classList.add('fade-in');
    }

    downloadFile() {
        if (this.downloadUrl) {
            const filename = this.downloadFilename || 'converted_file';
            const link = document.createElement('a');
            link.href = this.downloadUrl;
            link.download = filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // ダウンロード後の処理
            setTimeout(() => {
                this.reset();
            }, 1000);
        } else {
            this.showError('ダウンロード用データが見つかりません');
        }
    }

    showProgress(message, percentage) {
        const progressSection = document.getElementById('progress-section');
        const progressBar = document.querySelector('.progress-bar');
        const progressText = progressSection.querySelector('p');

        progressSection.classList.remove('hidden');
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = message;
    }

    updateProgress(percentage) {
        const progressBar = document.querySelector('.progress-bar');
        progressBar.style.width = `${percentage}%`;
    }

    hideProgress() {
        const progressSection = document.getElementById('progress-section');
        progressSection.classList.add('hidden');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle mr-2"></i>
            ${message}
        `;

        document.body.appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    getFileIcon(fileType) {
        const icons = {
            image: 'fas fa-image text-purple-600',
            video: 'fas fa-video text-blue-600',
            audio: 'fas fa-music text-green-600'
        };
        return icons[fileType] || 'fas fa-file text-gray-600';
    }

    reset() {
        if (this.downloadUrl) {
            URL.revokeObjectURL(this.downloadUrl);
        }

        this.currentFile = null;
        this.fileType = null;
        this.downloadUrl = null;
        this.downloadFilename = null;
        this.isConverting = false;

        // UIをリセット
        document.getElementById('upload-section').classList.remove('hidden');
        document.getElementById('file-info').classList.add('hidden');
        document.getElementById('progress-section').classList.add('hidden');
        document.getElementById('result-section').classList.add('hidden');

        // ファイル入力をリセット
        document.getElementById('file-input').value = '';

        // フォームをリセット
        document.getElementById('output-format').value = '';
        document.getElementById('quality').value = 'medium';
        document.getElementById('width').value = '';
        document.getElementById('height').value = '';
    }
}

// アプリケーションを初期化
document.addEventListener('DOMContentLoaded', () => {
    new MediaForge();
});
