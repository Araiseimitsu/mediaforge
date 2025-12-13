from pydub import AudioSegment
from pydub import utils as pydub_utils
import os
import shutil
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

# mediainfo_jsonの元の関数を保存
_original_mediainfo_json = pydub_utils.mediainfo_json

def _patched_mediainfo_json(filepath, read_ahead_limit=-1):
    """
    ffprobeが見つからない場合でも動作するようにパッチされたmediainfo_json
    """
    try:
        # 元の関数を試す
        return _original_mediainfo_json(filepath, read_ahead_limit)
    except FileNotFoundError:
        # ffprobeが見つからない場合、ダミーの情報を返す
        logger.warning(f"ffprobeが見つかりません。デフォルト値を使用します: {filepath}")

        # ファイル拡張子から形式を推測
        file_ext = Path(filepath).suffix.lower()
        codec_map = {
            '.mp3': 'mp3',
            '.wav': 'pcm_s16le',
            '.flac': 'flac',
            '.ogg': 'vorbis',
            '.m4a': 'aac',
            '.aac': 'aac'
        }
        codec_name = codec_map.get(file_ext, 'unknown')

        return {
            "streams": [
                {
                    "codec_name": codec_name,
                    "codec_type": "audio",
                    "sample_rate": "44100",
                    "channels": 2,
                    "bit_rate": "192000",
                    "bits_per_sample": 16
                }
            ],
            "format": {
                "duration": "0",
                "size": str(os.path.getsize(filepath)) if os.path.exists(filepath) else "0",
                "bit_rate": "192000"
            }
        }
    except Exception as e:
        # その他のエラーの場合もダミー情報を返す
        logger.warning(f"mediainfo取得エラー: {e}. デフォルト値を使用します")
        return {
            "streams": [
                {
                    "codec_name": "unknown",
                    "codec_type": "audio",
                    "sample_rate": "44100",
                    "channels": 2,
                    "bit_rate": "192000",
                    "bits_per_sample": 16
                }
            ],
            "format": {
                "duration": "0",
                "size": "0",
                "bit_rate": "192000"
            }
        }

# pydubのmediainfo_json関数をパッチ
pydub_utils.mediainfo_json = _patched_mediainfo_json

# audio_segmentモジュール内の参照もパッチ
try:
    from pydub import audio_segment
    audio_segment.mediainfo_json = _patched_mediainfo_json
except Exception as e:
    logger.warning(f"audio_segmentモジュールのパッチに失敗: {e}")

class AudioConverter:
    def __init__(self):
        self.supported_formats = {
            'input': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
            'output': ['mp3', 'wav', 'flac', 'aac', 'ogg']
        }
        self.ffmpeg_path = self._get_ffmpeg_path()
        self._configure_pydub()

    def _get_ffmpeg_path(self):
        """
        FFmpegのパスを取得（imageio-ffmpegまたはシステム）
        """
        try:
            # まず imageio-ffmpeg を試す
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            logger.info(f"imageio-ffmpegを使用: {ffmpeg_path}")
            return ffmpeg_path
        except ImportError:
            # imageio-ffmpeg がない場合、システムのFFmpegを探す
            system_ffmpeg = shutil.which('ffmpeg')
            if system_ffmpeg:
                logger.info(f"システムのFFmpegを使用: {system_ffmpeg}")
                return system_ffmpeg
            else:
                raise RuntimeError(
                    "FFmpegが見つかりません。\n"
                    "以下のいずれかの方法でインストールしてください:\n\n"
                    "方法1（推奨）: pip install imageio-ffmpeg\n"
                    "方法2（システムレベル）:\n"
                    "  Windows: choco install ffmpeg\n"
                    "  macOS: brew install ffmpeg\n"
                    "  Ubuntu/Debian: sudo apt install ffmpeg"
                )

    def _configure_pydub(self):
        """
        PydubにFFmpegのパスを設定
        """
        import warnings

        # FFmpegのディレクトリを取得
        ffmpeg_dir = os.path.dirname(self.ffmpeg_path)

        # ffmpeg.exeという名前のコピーを作成（Pydubが期待する名前）
        standard_ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        if not os.path.exists(standard_ffmpeg_path):
            try:
                import shutil
                shutil.copy2(self.ffmpeg_path, standard_ffmpeg_path)
                logger.info(f"FFmpegを標準名でコピー: {standard_ffmpeg_path}")
            except Exception as e:
                logger.warning(f"FFmpegのコピーに失敗: {e}")
                # コピーに失敗した場合は元のパスを使用
                standard_ffmpeg_path = self.ffmpeg_path

        # Pydubの設定（標準名のパスを使用）
        AudioSegment.converter = standard_ffmpeg_path
        AudioSegment.ffmpeg = standard_ffmpeg_path

        # 環境変数も設定（より確実）
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        os.environ['FFMPEG_BINARY'] = standard_ffmpeg_path

        # ffprobeのパスも設定（Windows環境用）
        # ffmpegとffprobeは通常同じディレクトリにある
        ffprobe_path = self.ffmpeg_path.replace('ffmpeg-win-x86_64', 'ffprobe-win-x86_64')
        if not os.path.exists(ffprobe_path):
            # 別のパターンを試す
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')

        if os.path.exists(ffprobe_path):
            AudioSegment.ffprobe = ffprobe_path
            os.environ['FFPROBE_BINARY'] = ffprobe_path
            logger.info(f"Pydub設定完了: FFmpeg={standard_ffmpeg_path}, FFprobe={ffprobe_path}")
        else:
            logger.info(f"Pydub設定完了: FFmpeg={standard_ffmpeg_path}, FFprobe=未検出")

        # Pydubの警告を抑制
        warnings.filterwarnings('ignore', message="Couldn't find ffmpeg or avconv")
        warnings.filterwarnings('ignore', message="Couldn't find ffprobe or avprobe")
    
    def _load_audio_file(self, file_path: Union[str, Path]) -> AudioSegment:
        """
        音声ファイルを読み込む（ffprobe不要の方法）
        """
        file_ext = Path(file_path).suffix.lower()

        # 拡張子に応じた読み込みメソッドを使用（ffprobe不要）
        format_map = {
            '.mp3': 'mp3',
            '.wav': 'wav',
            '.flac': 'flac',
            '.ogg': 'ogg',
            '.m4a': 'mp4',
            '.aac': 'aac'
        }

        file_format = format_map.get(file_ext)
        if not file_format:
            # 不明な形式の場合はfrom_fileを使用（ffprobeが必要）
            logger.warning(f"不明な形式: {file_ext}, from_fileを使用します")
            return AudioSegment.from_file(str(file_path))

        # 形式を明示的に指定して読み込み（ffprobe不要）
        logger.info(f"形式を指定して読み込み: {file_format}")
        return AudioSegment.from_file(str(file_path), format=file_format)

    async def convert(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        output_format: str,
        quality: Optional[str] = None
    ):
        """
        音声を変換する

        Args:
            input_path: 入力ファイルパス
            output_path: 出力ファイルパス
            output_format: 出力形式 (mp3, wav, flac, aac, ogg)
            quality: 品質設定 (high, medium, low)
        """
        try:
            logger.info(f"音声変換開始: {input_path} -> {output_path} (形式: {output_format}, 品質: {quality})")

            # 音声ファイルを読み込む（ffprobe不要の方法）
            logger.info(f"音声ファイル読み込み中: {input_path}")
            audio = self._load_audio_file(input_path)
            logger.info(f"音声ファイル読み込み成功: 長さ={len(audio)}ms, チャンネル={audio.channels}")

            # 出力形式と品質設定
            export_params = self._get_export_params(output_format, quality)
            logger.info(f"エクスポートパラメータ: {export_params}")

            # フォーマット名のマッピング（FFmpegが期待する名前に変換）
            format_mapping = {
                'aac': 'adts',  # AACの場合はADTS形式を使用
                'mp3': 'mp3',
                'wav': 'wav',
                'flac': 'flac',
                'ogg': 'ogg'
            }

            ffmpeg_format = format_mapping.get(output_format.lower(), output_format.lower())

            # 音声を変換して保存
            logger.info(f"音声変換実行中... (FFmpegフォーマット: {ffmpeg_format})")
            audio.export(
                str(output_path),
                format=ffmpeg_format,
                **export_params
            )
            logger.info(f"音声変換成功: {output_path}")

        except Exception as e:
            logger.error(f"音声変換エラー: {str(e)}", exc_info=True)
            raise Exception(f"音声変換エラー: {str(e)}")
    
    def _get_export_params(self, output_format: str, quality: Optional[str]) -> dict:
        """
        出力パラメータを取得
        """
        quality_settings = {
            'high': {'bitrate': '320k'},
            'medium': {'bitrate': '192k'},
            'low': {'bitrate': '128k'}
        }
        
        base_params = {}
        
        if output_format.lower() in ['mp3', 'aac', 'ogg']:
            base_params.update(quality_settings.get(quality, quality_settings['medium']))
        
        if output_format.lower() == 'mp3':
            base_params.update({
                'codec': 'libmp3lame',
                'parameters': ['-q:a', str(2 if quality == 'high' else 5 if quality == 'medium' else 9)]
            })
        elif output_format.lower() == 'aac':
            base_params.update({
                'codec': 'aac',
                'parameters': ['-b:a', quality_settings.get(quality, quality_settings['medium'])['bitrate']]
            })
        elif output_format.lower() == 'ogg':
            base_params.update({
                'codec': 'libvorbis'
            })
        elif output_format.lower() == 'flac':
            base_params.update({
                'codec': 'flac',
                'parameters': ['-compression_level', '8']
            })
        elif output_format.lower() == 'wav':
            base_params.update({
                'codec': 'pcm_s16le'
            })
        
        return base_params
    
    def get_audio_info(self, audio_path: Union[str, Path]) -> dict:
        """
        音声情報を取得する
        """
        try:
            audio = self._load_audio_file(audio_path)
            
            return {
                'duration_seconds': len(audio) / 1000.0,
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'frame_count': len(audio),
                'file_size': os.path.getsize(audio_path),
                'max_dBFS': audio.max_dBFS,
                'duration_ms': len(audio)
            }
            
        except Exception as e:
            raise Exception(f"音声情報取得エラー: {str(e)}")
    
    async def trim_audio(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        start_time: float,
        end_time: float,
        output_format: str = "mp3"
    ):
        """
        音声をトリミングする

        Args:
            input_path: 入力ファイルパス
            output_path: 出力ファイルパス
            start_time: 開始時間（秒）
            end_time: 終了時間（秒）
            output_format: 出力形式
        """
        try:
            audio = self._load_audio_file(input_path)
            
            # ミリ秒に変換
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            # トリミング
            trimmed_audio = audio[start_ms:end_ms]
            
            # 保存
            export_params = self._get_export_params(output_format, 'medium')
            trimmed_audio.export(str(output_path), format=output_format, **export_params)
            
        except Exception as e:
            raise Exception(f"音声トリミングエラー: {str(e)}")
    
    async def adjust_volume(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        volume_change_db: float,
        output_format: str = "mp3"
    ):
        """
        音量を調整する

        Args:
            input_path: 入力ファイルパス
            output_path: 出力ファイルパス
            volume_change_db: 音量変更量（dB）
            output_format: 出力形式
        """
        try:
            audio = self._load_audio_file(input_path)
            
            # 音量調整
            adjusted_audio = audio + volume_change_db
            
            # 保存
            export_params = self._get_export_params(output_format, 'medium')
            adjusted_audio.export(str(output_path), format=output_format, **export_params)
            
        except Exception as e:
            raise Exception(f"音量調整エラー: {str(e)}")
