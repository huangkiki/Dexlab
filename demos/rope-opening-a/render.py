"""Render an Opening A replay from a recorded solver trajectory."""

import argparse
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 1280, 720
SCALE = 1370
PALM_ORIGIN = np.array([WIDTH / 2, 413.0])
FPS = 60


def cubic_path(start, segments):
    points = [np.asarray(start)]
    for control_a, control_b, end in segments:
        a, b, c, d = map(np.asarray, (points[-1], control_a, control_b, end))
        for t in np.linspace(0, 1, 18)[1:]:
            points.append((1-t)**3 * a + 3*t*(1-t)**2 * b + 3*t*t*(1-t) * c + t**3 * d)
    return [(float(x), float(y)) for x, y in points]


def palm_illustration():
    size = (245, 540)
    origin = np.array([129, 302])
    outline = cubic_path((-32, 118), [
        ((-48, 94), (-54, 64), (-61, 42)),
        ((-69, 17), (-89, -6), (-102, -26)),
        ((-117, -49), (-107, -62), (-91, -54)),
        ((-74, -47), (-65, -40), (-52, -24)),
        ((-48, -55), (-62, -119), (-73, -168)),
        ((-82, -207), (-91, -232), (-76, -233)),
        ((-64, -235), (-52, -210), (-42, -185)),
        ((-50, -224), (-66, -270), (-50, -276)),
        ((-35, -281), (-22, -251), (-12, -214)),
        ((-20, -242), (-31, -266), (-16, -268)),
        ((-1, -270), (9, -245), (19, -211)),
        ((25, -191), (29, -169), (34, -145)),
        ((35, -164), (31, -187), (43, -188)),
        ((58, -190), (65, -159), (66, -130)),
        ((68, -102), (71, -70), (61, -48)),
        ((54, -29), (57, -3), (48, 29)),
        ((40, 58), (26, 77), (24, 100)),
        ((22, 116), (29, 126), (31, 140)),
        ((12, 132), (-12, 125), (-32, 118)),
    ])
    silhouette = Image.new("L", size)
    ImageDraw.Draw(silhouette).polygon([tuple(origin + p) for p in outline], fill=255)
    soft = np.array(silhouette.filter(ImageFilter.GaussianBlur(15)), dtype=float) / 255
    dy, dx = np.gradient(soft)
    y, x = np.mgrid[:size[1], :size[0]].astype(float)
    x -= origin[0]
    y -= origin[1]
    palm = np.exp(-((x + 8) / 55)**2 - ((y + 11) / 73)**2)
    fingers = np.exp(-((x + 22) / 61)**2 - ((y + 170) / 118)**2)
    intensity = 0.55 + 0.22 * soft + 6.0 * (-dx - 0.35 * dy) + 0.18 * palm + 0.13 * fingers
    rgb = intensity[:, :, None] * np.array([190, 151, 122])
    image = Image.fromarray(np.uint8(np.clip(rgb, 0, 255))).convert("RGBA")
    detail = Image.new("RGBA", size)
    draw = ImageDraw.Draw(detail)
    creases = [
        ((-45, -22), [((-14, -10), (-5, 20), (-27, 54))]),
        ((-35, -51), [((-9, -27), (20, -25), (43, -46))]),
        ((-30, -83), [((-11, -68), (24, -67), (48, -80))]),
        ((-65, -164), [((-55, -169), (-49, -170), (-45, -166))]),
        ((-32, -191), [((-21, -196), (-13, -197), (-9, -194))]),
        ((-4, -184), [((7, -189), (13, -188), (20, -186))]),
    ]
    for start, path in creases:
        draw.line([tuple(origin + p) for p in cubic_path(start, path)],
                  fill=(72, 40, 29, 132), width=2)
    image.alpha_composite(detail.filter(ImageFilter.GaussianBlur(1.7)))
    image.putalpha(silhouette.filter(ImageFilter.GaussianBlur(0.8)))
    sleeve = Image.new("RGBA", size)
    draw = ImageDraw.Draw(sleeve)
    sleeve_path = cubic_path((-39, 95), [
        ((-16, 106), (7, 123), (32, 121)),
        ((58, 158), (65, 217), (66, 239)),
        ((20, 245), (-34, 237), (-69, 239)),
        ((-63, 197), (-49, 131), (-39, 95)),
    ])
    draw.polygon([tuple(origin + p) for p in sleeve_path], fill=(20, 25, 28, 255))
    draw.line([tuple(origin + p) for p in sleeve_path[:18]], fill=(54, 57, 55, 255), width=2)
    image.alpha_composite(sleeve.filter(ImageFilter.GaussianBlur(0.8)))
    return image, origin


def background():
    y, x = np.mgrid[:HEIGHT, :WIDTH]
    glow = np.exp(-((x - WIDTH/2) / 520)**2 - ((y - 390) / 275)**2)
    color = np.array([9, 13, 17]) + glow[:, :, None] * np.array([14, 19, 24])
    image = Image.fromarray(np.uint8(color))
    draw = ImageDraw.Draw(image)
    draw.text((53, 47), "Opening A", font=ImageFont.load_default(size=27), fill="#eeede5")
    draw.text((55, 83), "DexLab  /  libuipc", font=ImageFont.load_default(size=15), fill="#a2b0b4")
    return image


def project(points):
    return PALM_ORIGIN + SCALE * np.stack((points[..., 0], -points[..., 1]), axis=-1)


def draw_frame(backdrop, left_palm, right_palm, origin, points, edges, guides):
    image = backdrop.copy()
    centers = project(guides[:, :3, 3])
    for palm, center, pivot in zip(
        (left_palm, right_palm), centers, (origin, np.array([left_palm.width - 1 - origin[0], origin[1]])),
    ):
        image.paste(palm, tuple(np.rint(center - pivot).astype(int)), palm)
    rope = project(points)
    lower = np.maximum(np.floor(rope.min(axis=0)).astype(int) - 5, 0)
    upper = np.minimum(np.ceil(rope.max(axis=0)).astype(int) + 5, (WIDTH, HEIGHT))
    size = upper - lower
    if np.all(size > 0):
        rope_layer = Image.new("RGBA", tuple(3 * size))
        rope = 3 * (rope - lower)
        draw = ImageDraw.Draw(rope_layer)
        for offset, color, width in ((2, "#121718", 14), (0, "#eee9d5", 9), (-2, "#fff9ea", 3)):
            for a, b in edges:
                x0, y0 = rope[a]
                x1, y1 = rope[b]
                draw.line(((x0, y0 + offset), (x1, y1 + offset)), fill=color, width=width)
        rope_layer = rope_layer.resize(tuple(size), Image.Resampling.LANCZOS)
        image.paste(rope_layer, tuple(lower), rope_layer)
    return image


def render(trajectory, output):
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("Install FFmpeg with the libx264 encoder")
    with np.load(trajectory) as record:
        points, edges, guides, times = (record[key] for key in ("positions", "edges", "transforms", "times"))
    if (times.shape != (241,) or points.ndim != 3 or points.shape[0] != len(times)
            or points.shape[-1] != 3 or guides.shape != (241, 2, 4, 4)
            or not np.isfinite(points).all() or not np.isfinite(guides).all()):
        raise ValueError("A complete 241-frame trajectory is required")
    output.mkdir(parents=True)
    backdrop = background()
    left_palm, origin = palm_illustration()
    right_palm = left_palm.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    command = [
        ffmpeg, "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-threads", "4", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output / "opening-a.mp4"),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for frame in range(0, len(times), 2):
            image = draw_frame(backdrop, left_palm, right_palm, origin, points[frame], edges, guides[frame])
            encoder.stdin.write(image.tobytes())
        image.save(output / "opening-a.png")
        still = image.tobytes()
        for _ in range(FPS):
            encoder.stdin.write(still)
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError("FFmpeg could not encode the replay")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trajectory", type=Path)
    parser.add_argument("output", type=Path, help="New directory for the MP4 and poster")
    args = parser.parse_args()
    render(args.trajectory, args.output)
