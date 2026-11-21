"""จับคู่ PC กับทีวี LG (ทำครั้งเดียว)

วิธีใช้:  python pair_lgtv.py 192.168.1.50
ดู IP ทีวีได้ที่ Settings → Network → Wi-Fi/Wired → Advanced
"""
import sys

from gta6sub.lgtv import pair

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("ใช้แบบนี้: python pair_lgtv.py <IP ของทีวี>")
    pair(sys.argv[1])
