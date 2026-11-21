"""ลากกรอบเลือกตำแหน่งซับภาษาอังกฤษในเกม แล้วบันทึกลง config.yaml

วิธีใช้: เปิดเกมให้มีซับขึ้นจอ แล้วรัน  python calibrate.py
ลากเมาส์ครอบบริเวณซับ (เผื่อ 2 บรรทัด) กด Enter/Space เพื่อบันทึก, กด c เพื่อยกเลิก
"""
import argparse

import cv2

from gta6sub.capture import crop_region, open_source
from gta6sub.config import load_config, save_region


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", default="config.yaml")
    args = ap.parse_args()
    cfg = load_config(args.config)

    src = open_source(cfg)
    frame = src.read()
    src.close()
    if frame is None:
        raise SystemExit("อ่านภาพจากแหล่งภาพไม่ได้")

    h, w = frame.shape[:2]
    scale = min(1.0, 1280 / w)
    preview = cv2.resize(frame, None, fx=scale, fy=scale)
    x, y, rw, rh = cv2.selectROI("Select subtitle area", preview, showCrosshair=False)
    cv2.destroyAllWindows()
    if rw == 0 or rh == 0:
        raise SystemExit("ยกเลิก")

    pw, ph = preview.shape[1], preview.shape[0]
    region = {"left": x / pw, "top": y / ph, "width": rw / pw, "height": rh / ph}
    save_region(args.config, region)
    print("บันทึกแล้ว:", region)

    from gta6sub.ocr import SubtitleOCR

    text = SubtitleOCR(cfg["min_confidence"]).read(crop_region(frame, region))
    print("ทดสอบ OCR อ่านได้ว่า:", text or "(ไม่พบข้อความ)")


if __name__ == "__main__":
    main()
