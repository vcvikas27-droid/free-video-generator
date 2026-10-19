#!/usr/bin/env python3
"""Generate a no-paid-API Hindi YouTube Short (vertical MP4) using Edge TTS + FFmpeg."""
import asyncio, os, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

OUT = Path(os.environ.get("OUTPUT_DIR", "output"))
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1080, 1920
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
if not Path(FONT_PATH).exists():
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf"
TITLE_FONT = ImageFont.truetype(FONT_PATH, 84)
BODY_FONT = ImageFont.truetype(FONT_PATH, 62)
SMALL_FONT = ImageFont.truetype(FONT_PATH, 36)
SCENES = [
    ("आज की बात", "सफलता एक दिन में नहीं मिलती।", "हर दिन की छोटी कोशिश मायने रखती है।", (16, 28, 65), (30, 110, 150)),
    ("रुकना मत", "धीरे चलना ठीक है,", "लेकिन अपने लक्ष्य की तरफ चलते रहो।", (47, 20, 75), (150, 48, 96)),
    ("याद रखना", "आज की मेहनत ही", "कल का आत्मविश्वास बनती है।", (9, 65, 65), (20, 130, 100)),
]
NARRATION = "आज की बात। सफलता एक दिन में नहीं मिलती। हर दिन की छोटी कोशिश मायने रखती है। धीरे चलना ठीक है, लेकिन अपने लक्ष्य की तरफ चलते रहो। आज की मेहनत ही कल का आत्मविश्वास बनती है। अगर बात अच्छी लगी, तो इसे याद रखना और अपने लक्ष्य पर काम करते रहना।"

def make_card(index, scene):
    title, line1, line2, c1, c2 = scene
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        col = tuple(int(c1[k] * (1-t) + c2[k] * t) for k in range(3))
        for x in range(W):
            px[x, y] = col
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((70, 100, W-70, H-100), radius=48, outline=(255,255,255), width=4)
    d.text((W//2, 400), title, font=TITLE_FONT, fill=(255, 220, 110), anchor="mm", stroke_width=2, stroke_fill=(20,20,30))
    d.rounded_rectangle((120, 650, W-120, 1260), radius=40, fill=(0,0,0), outline=(255,255,255), width=2)
    d.multiline_text((W//2, 850), "\n".join(textwrap.wrap(line1, 17)), font=BODY_FONT, fill="white", anchor="mm", align="center", spacing=24, stroke_width=1, stroke_fill=(0,0,0))
    d.multiline_text((W//2, 1080), "\n".join(textwrap.wrap(line2, 17)), font=BODY_FONT, fill=(210,245,255), anchor="mm", align="center", spacing=24, stroke_width=1, stroke_fill=(0,0,0))
    d.text((W//2, 1500), "DAILY MOTIVATION  •  HINDI SHORTS", font=SMALL_FONT, fill=(255,255,255), anchor="mm")
    d.text((W//2, 1770), f"{index+1} / {len(SCENES)}", font=SMALL_FONT, fill=(255,255,255), anchor="mm")
    path = OUT / f"scene_{index}.png"
    im.save(path)
    return path

async def main():
    audio = OUT / "narration.mp3"
    communicate = edge_tts.Communicate(NARRATION, voice="hi-IN-MadhurNeural", rate="+4%")
    await communicate.save(str(audio))
    cards = [make_card(i, s) for i, s in enumerate(SCENES)]
    # 3 scenes, 8 seconds each; narration audio spans the whole video.
    inputs = []
    for p in cards:
        inputs += ["-loop", "1", "-t", "8", "-i", str(p)]
    inputs += ["-i", str(audio)]
    filters = (
        "[0:v]scale=1080:1920,setsar=1[v0];"
        "[1:v]scale=1080:1920,setsar=1[v1];"
        "[2:v]scale=1080:1920,setsar=1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0,format=yuv420p[v]"
    )
    final = OUT / "hindi_motivation_short.mp4"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filters, "-map", "[v]", "-map", "3:a", "-t", "24", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(final)]
    subprocess.run(cmd, check=True)
    print(f"VIDEO_READY={final.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
