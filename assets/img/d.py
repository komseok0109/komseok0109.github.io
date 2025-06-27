from PIL import Image
import os
import sys

if len(sys.argv) != 2:
    print("사용법: python convert_png_to_webp.py [하위폴더명]")
    sys.exit(1)

subfolder_name = sys.argv[1]
base_folder = os.path.dirname(os.path.abspath(__file__))
target_folder = os.path.join(base_folder, subfolder_name)

if not os.path.isdir(target_folder):
    print(f"[오류] 폴더가 존재하지 않습니다: {target_folder}")
    sys.exit(1)

converted = 0
for filename in os.listdir(target_folder):
    if filename.lower().endswith('.png'):
        png_path = os.path.join(target_folder, filename)
        webp_path = os.path.splitext(png_path)[0] + '.webp'

        try:
            with Image.open(png_path) as img:
                img.save(webp_path, 'WEBP')
            os.remove(png_path)
            converted += 1
            print(f"✅ {filename} → {os.path.basename(webp_path)} (원본 삭제됨)")
        except Exception as e:
            print(f"❌ 변환 실패: {filename} → {e}")

print(f"\n총 변환된 파일 수: {converted}개")
