class MediaForge {
    constructor() {
        this.currentFile = null;
        this.fileId = null;
        this.downloadUrl = null;
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

        this.currentFile = file;

        // ファイルをアップロード
        await this.uploadFile(file);
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            this.showProgress('アップロード中...', 10);

            const response = await fetch('/api/convert/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('ファイルのアップロードに失敗しました');
            }

            const result = await response.json();
            this.fileId = result.file_id;

            // ファイル情報を表示
            this.showFileInfo(result);

            // サポート形式を取得
            await this.loadSupportedFormats(result.file_type);

            this.hideProgress();

        } catch (error) {
            this.showError(error.message);
            this.hideProgress();
        }
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
                    <p class="text-sm text-gray-500">${fileSize} • ${fileInfo.file_type.toUpperCase()}</p>
                </div>
            </div>
        `;

        fileInfoSection.classList.remove('hidden');
        fileInfoSection.classList.add('fade-in');
    }

    async loadSupportedFormats(fileType) {
        try {
            const response = await fetch(`/api/convert/formats/${fileType}`);
            const result = await response.json();

            const formatSelect = document.getElementById('output-format');
            formatSelect.innerHTML = '<option value="">選択してください</option>';

            result.formats.forEach(format => {
                const option = document.createElement('option');
                option.value = format;
                option.textContent = format.toUpperCase();
                formatSelect.appendChild(option);
            });

        } catch (error) {
            console.error('形式の取得に失敗しました:', error);
        }
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

    async startConversion() {
        const outputFormat = document.getElementById('output-format').value;
        const quality = document.getElementById('quality').value;
        const width = document.getElementById('width').value;
        const height = document.getElementById('height').value;

        if (!outputFormat) {
            this.showError('出力形式を選択してください');
            return;
        }

        if (!this.fileId) {
            this.showError('ファイルがアップロードされていません');
            return;
        }

        const formData = new FormData();
        formData.append('file_id', this.fileId);
        formData.append('output_format', outputFormat);
        formData.append('quality', quality);

        if (width) formData.append('width', width);
        if (height) formData.append('height', height);

        try {
            this.showProgress('変換中...', 50);

            // 変換オプションを非表示
            document.getElementById('file-info').classList.add('hidden');

            const response = await fetch('/api/convert/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '変換に失敗しました');
            }

            const result = await response.json();
            this.downloadUrl = result.download_url;

            this.updateProgress(100);
            setTimeout(() => {
                this.showResult(result);
            }, 500);

        } catch (error) {
            this.showError(error.message);
            this.hideProgress();
        }
    }

    showResult(result) {
        const progressSection = document.getElementById('progress-section');
        const resultSection = document.getElementById('result-section');
        const resultInfo = document.getElementById('result-info');

        progressSection.classList.add('hidden');

        resultInfo.innerHTML = `
            <p class="text-gray-700">
                <i class="fas fa-check-circle text-green-600 mr-2"></i>
                ファイルが正常に変換されました
            </p>
        `;

        resultSection.classList.remove('hidden');
        resultSection.classList.add('fade-in');
    }

    downloadFile() {
        if (this.downloadUrl) {
            // ダウンロードURLからファイル名を抽出
            const filename = this.downloadUrl.split('/').pop();
            const link = document.createElement('a');
            link.href = this.downloadUrl;
            link.download = filename || 'converted_file';
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // ダウンロード後の処理
            setTimeout(() => {
                this.reset();
            }, 1000);
        } else {
            this.showError('ダウンロードURLが見つかりません');
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
        // エラーメッセージを表示
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
            'image': 'fas fa-image text-purple-600',
            'video': 'fas fa-video text-blue-600',
            'audio': 'fas fa-music text-green-600'
        };
        return icons[fileType] || 'fas fa-file text-gray-600';
    }

    reset() {
        // アプリケーション状態をリセット
        this.currentFile = null;
        this.fileId = null;
        this.downloadUrl = null;

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
