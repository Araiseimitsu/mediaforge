import ffmpeg
import os
import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

class VideoConverter:
    def __init__(self):
        self.supported_formats = {
            'input': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
            'output': ['mp4', 'avi', 'mov', 'mkv', 'webm', 'gif']
        }
        self.ffmpeg_path = self._get_ffmpeg_path()

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

    async def convert(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        output_format: str,
        quality: Optional[str] = None
    ):
        """
        動画を変換する

        Args:
            input_path: 入力ファイルパス
            output_path: 出力ファイルパス
            output_format: 出力形式 (mp4, avi, mov, mkv, webm, gif)
            quality: 品質設定 (high, medium, low)
        """
        try:
            output_format = output_format.lower()

            if output_format == 'gif':
                await self._convert_to_gif(input_path, output_path, quality)
            elif output_format == 'webm':
                await self._convert_to_webm(input_path, output_path, quality)
            else:
                await self._convert_video(input_path, output_path, output_format, quality)

        except Exception as e:
            raise Exception(f"動画変換エラー: {str(e)}")
    
    async def _convert_video(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        output_format: str,
        quality: Optional[str] = None
    ):
        """
        通常の動画変換
        """
        try:
            # 品質設定
            quality_params = self._get_quality_params(quality)

            # 入力ストリーム
            input_stream = ffmpeg.input(str(input_path))

            # FFmpegフォーマット名のマッピング
            format_mapping = {
                'mkv': 'matroska',
                'mp4': 'mp4',
                'avi': 'avi',
                'mov': 'mov',
                'webm': 'webm'
            }

            ffmpeg_format = format_mapping.get(output_format, output_format)

            # 出力ストリームの設定
            output_stream = input_stream.output(
                str(output_path),
                vcodec=quality_params['vcodec'],
                acodec=quality_params['acodec'],
                video_bitrate=quality_params['video_bitrate'],
                audio_bitrate=quality_params['audio_bitrate'],
                crf=quality_params['crf'],
                preset=quality_params['preset'],
                format=ffmpeg_format
            )

            # 変換実行（非同期）
            await asyncio.to_thread(
                ffmpeg.run,
                output_stream,
                cmd=self.ffmpeg_path,
                overwrite_output=True,
                capture_stdout=True,
                capture_stderr=True
            )
            logger.info(f"動画変換成功: {input_path} -> {output_path}")

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpegエラー: {error_message}")
            raise Exception(f"動画変換に失敗しました: {error_message}")
    
    async def _convert_to_webm(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        quality: Optional[str] = None
    ):
        """
        動画をWebMに変換（VP8 + Vorbis）
        VP9は非常に遅いため、VP8を使用して高速化
        """
        try:
            logger.info(f"WebM変換を開始: {input_path} -> {output_path}")

            # 品質設定（WebM用）- VP8を使用して高速化
            quality_settings = {
                'high': {
                    'vcodec': 'libvpx',  # VP8（VP9より高速）
                    'acodec': 'libvorbis',  # Vorbis（Opusより互換性が高い）
                    'video_bitrate': '2000k',
                    'audio_bitrate': '192k',
                    'qmin': 10,
                    'qmax': 42,
                },
                'medium': {
                    'vcodec': 'libvpx',
                    'acodec': 'libvorbis',
                    'video_bitrate': '1000k',
                    'audio_bitrate': '128k',
                    'qmin': 10,
                    'qmax': 50,
                },
                'low': {
                    'vcodec': 'libvpx',
                    'acodec': 'libvorbis',
                    'video_bitrate': '500k',
                    'audio_bitrate': '96k',
                    'qmin': 10,
                    'qmax': 60,
                }
            }

            params = quality_settings.get(quality, quality_settings['medium'])

            # 入力ストリーム
            input_stream = ffmpeg.input(str(input_path))

            # 出力ストリームの設定（WebM用）
            output_stream = input_stream.output(
                str(output_path),
                vcodec=params['vcodec'],
                acodec=params['acodec'],
                video_bitrate=params['video_bitrate'],
                audio_bitrate=params['audio_bitrate'],
                qmin=params['qmin'],
                qmax=params['qmax'],
                format='webm',
                **{'cpu-used': 4}  # エンコード速度優先（-16～16、大きいほど速い）
            )

            logger.info("WebM変換処理を実行中...")

            # 変換実行（非同期）
            await asyncio.to_thread(
                ffmpeg.run,
                output_stream,
                cmd=self.ffmpeg_path,
                overwrite_output=True,
                capture_stdout=True,
                capture_stderr=True
            )
            logger.info(f"WebM変換成功: {input_path} -> {output_path}")

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"WebM変換エラー: {error_message}")
            raise Exception(f"WebM変換に失敗しました: {error_message}")

    async def _convert_to_gif(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        quality: Optional[str] = None
    ):
        """
        動画をGIFに変換
        """
        try:
            # パレット生成
            palette_path = Path(output_path).parent / f"{Path(output_path).stem}_palette.png"

            # パレットを生成
            palette_stream = (
                ffmpeg
                .input(str(input_path))
                .filter('fps', fps=15)
                .filter('scale', width=480, height=-1, flags='lanczos')
                .filter('palettegen')
                .output(str(palette_path))
                .overwrite_output()
            )

            await asyncio.to_thread(
                ffmpeg.run,
                palette_stream,
                cmd=self.ffmpeg_path,
                capture_stdout=True,
                capture_stderr=True
            )

            # パレットを使用してGIFを生成
            gif_stream = (
                ffmpeg
                .input(str(input_path))
                .filter('fps', fps=15)
                .filter('scale', width=480, height=-1, flags='lanczos')
                .output(str(output_path))
                .overwrite_output()
            )

            await asyncio.to_thread(
                ffmpeg.run,
                gif_stream,
                cmd=self.ffmpeg_path,
                capture_stdout=True,
                capture_stderr=True
            )

            # パレットファイルを削除
            if palette_path.exists():
                palette_path.unlink()

            logger.info(f"GIF変換成功: {input_path} -> {output_path}")

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"GIF変換エラー: {error_message}")
            raise Exception(f"GIF変換に失敗しました: {error_message}")
        except Exception as e:
            logger.error(f"予期しないエラー: {str(e)}")
            raise Exception(f"GIF変換中にエラーが発生しました: {str(e)}")
    
    def _get_quality_params(self, quality: Optional[str]) -> dict:
        """
        品質設定を取得
        """
        quality_settings = {
            'high': {
                'vcodec': 'libx264',
                'acodec': 'aac',
                'video_bitrate': '2000k',
                'audio_bitrate': '192k',
                'crf': 18,
                'preset': 'slow'
            },
            'medium': {
                'vcodec': 'libx264',
                'acodec': 'aac',
                'video_bitrate': '1000k',
                'audio_bitrate': '128k',
                'crf': 23,
                'preset': 'medium'
            },
            'low': {
                'vcodec': 'libx264',
                'acodec': 'aac',
                'video_bitrate': '500k',
                'audio_bitrate': '96k',
                'crf': 28,
                'preset': 'fast'
            }
        }
        
        return quality_settings.get(quality, quality_settings['medium'])
    
    def get_video_info(self, video_path: Union[str, Path]) -> dict:
        """
        動画情報を取得する
        """
        try:
            probe = ffmpeg.probe(str(video_path), cmd=self.ffmpeg_path.replace('ffmpeg', 'ffprobe'))
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            info = {
                'duration': float(probe['format']['duration']),
                'file_size': int(probe['format']['size']),
                'format_name': probe['format']['format_name']
            }
            
            if video_stream:
                info.update({
                    'width': int(video_stream['width']),
                    'height': int(video_stream['height']),
                    'video_codec': video_stream['codec_name'],
                    'fps': eval(video_stream['r_frame_rate'])
                })
            
            if audio_stream:
                info.update({
                    'audio_codec': audio_stream['codec_name'],
                    'sample_rate': int(audio_stream['sample_rate']),
                    'channels': int(audio_stream['channels'])
                })
            
            return info
            
        except Exception as e:
            raise Exception(f"動画情報取得エラー: {str(e)}")
