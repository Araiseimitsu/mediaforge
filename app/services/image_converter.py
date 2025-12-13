from PIL import Image, ImageOps
import os
from pathlib import Path
from typing import Optional, Union

class ImageConverter:
    def __init__(self):
        self.supported_formats = {
            'input': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
            'output': ['jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff']
        }
    
    async def convert(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        output_format: str,
        quality: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ):
        """
        画像を変換する
        
        Args:
            input_path: 入力ファイルパス
            output_path: 出力ファイルパス
            output_format: 出力形式 (jpeg, png, webp, gif, bmp, tiff)
            quality: 品質設定 (high, medium, low)
            width: 出力幅
            height: 出力高さ
        """
        try:
            # 画像を開く
            with Image.open(input_path) as img:
                # EXIF情報を保持して画像を正しい向きに回転
                img = ImageOps.exif_transpose(img)
                
                # RGBAモードをRGBに変換（JPEG対応のため）
                if output_format.lower() == 'jpeg' and img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # サイズ変更
                if width or height:
                    img = self._resize_image(img, width, height)
                
                # 品質設定
                save_kwargs = {}
                if output_format.lower() in ['jpeg', 'webp']:
                    quality_map = {'high': 95, 'medium': 75, 'low': 50}
                    save_kwargs['quality'] = quality_map.get(quality, 75)
                    save_kwargs['optimize'] = True
                
                # 画像を保存
                img.save(output_path, format=output_format.upper(), **save_kwargs)
                
        except Exception as e:
            raise Exception(f"画像変換エラー: {str(e)}")
    
    def _resize_image(self, img: Image.Image, width: Optional[int], height: Optional[int]) -> Image.Image:
        """
        画像をリサイズする。アスペクト比を保持する。
        """
        if width and height:
            # 両方指定されている場合は指定サイズに
            return img.resize((width, height), Image.Resampling.LANCZOS)
        elif width:
            # 幅のみ指定の場合はアスペクト比を保持して高さを計算
            ratio = width / img.width
            height = int(img.height * ratio)
            return img.resize((width, height), Image.Resampling.LANCZOS)
        elif height:
            # 高さのみ指定の場合はアスペクト比を保持して幅を計算
            ratio = height / img.height
            width = int(img.width * ratio)
            return img.resize((width, height), Image.Resampling.LANCZOS)
        else:
            return img
    
    def get_image_info(self, image_path: Union[str, Path]) -> dict:
        """
        画像情報を取得する
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size': os.path.getsize(image_path)
                }
        except Exception as e:
            raise Exception(f"画像情報取得エラー: {str(e)}")
