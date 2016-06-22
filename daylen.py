#!/usr/bin/env python3

import colorsys
import datetime
import sys

import astral

from PIL import Image, ImageDraw, ImageFont

IMAGE_FN = "azmap.png"
FONT_FN = "/usr/share/fonts/TTF/calibri.ttf"

DEGREE_TO_PX = 12.84
MIN_LATITUDE = 23
MAX_LATITUDE = 90

MIN_SEPARATION_DEG = 2.5
GRAD_START_COLOR = (160, 0, 0)
GRAD_END_COLOR = (0, 160, 0)



def prerr(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def outline_latitude(img, latitude, string="", font_size=20, thickness=3, color=(200, 0, 0)):

    """ Outline a latitude with a circle of given thickness and color. Uses
    a mask layer to overcome the lack of a thickness option in PIL's ellipse
    method.
    """

    r = (90 - latitude) * DEGREE_TO_PX
    center_x = img.size[0] / 2
    center_y = img.size[1] / 2

    font = ImageFont.truetype(FONT_FN, font_size)
    (text_w, text_h) = font.getsize(string)

    # Create mask + composite images

    ell_layer = \
        Image.new(img.mode, img.size, color=color)
    mask = Image.new("L", img.size)
    mask_dc = ImageDraw.Draw(mask)
    half_t = thickness / 2

    for (rdelta, fill) in ((-half_t, 255), (half_t, 0)):
        mask_dc.ellipse(
            [
                center_x - r + rdelta, center_y - r + rdelta,
                center_x + r - rdelta, center_y + r - rdelta
            ],
            fill=fill
        )

    if (string):
        gap_size = text_w + thickness * 2
        half_gap_size = gap_size / 2
        mask_dc.rectangle(
            [
                center_x - half_gap_size, center_y + r - half_gap_size,
                center_x + half_gap_size, center_y + r + half_gap_size
            ],
            fill=0
        )

    img = Image.composite(ell_layer, img, mask)

    # Apply text

    if (string):
        dc = ImageDraw.Draw(img)
        text_x = center_x - text_w / 2
        text_y = center_y + r - text_h / 2

        dc.text((text_x, text_y), string, font=font, fill=color)

    return img

def hsl_gradient(val, min_val, max_val, start_rgb, end_rgb):

    """ Return a RGB position on a HSL gradient. RGB tuples have values in
    the range [0 .. 255].
    """

    if (val < min_val):
        val = min_val
    elif (val > max_val):
        val = max_val

    start = colorsys.rgb_to_hls( \
        start_rgb[0] / 255, start_rgb[1] / 255, start_rgb[2] / 255)
    end = colorsys.rgb_to_hls( \
        end_rgb[0] / 255, end_rgb[1] / 255, end_rgb[2] / 255)
    hls = [0, 0, 0]

    for i in range(3):
        ch_delta = end[i] - start[i]
        val_range = max_val - min_val
        normal_val = val - min_val
        normal_max_val = max_val - min_val

        hls[i] = start[i] + ch_delta * (normal_val / normal_max_val)

    rgb = colorsys.hls_to_rgb(*hls)
    return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

def debug_hsl_gradient(img, *extra):
    min_val = extra[0]
    max_val = extra[1]
    dim = 50
    dc = ImageDraw.Draw(img)

    for i in range(min_val, max_val + 1):
        color = hsl_gradient(i, *extra)
        pos = i - min_val
        dc.rectangle([0 + pos*dim, 0, 0 + pos*dim + dim, dim], fill=color)

def print_date(img, date, font_size=40, padding=10):
    dc = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_FN, font_size)
    date_str = date.strftime("%b %d")

    dc.text((padding, padding), date_str, font=font, fill=(20, 20, 20))

def get_isoline_latitude(date, daylen):
    loc = astral.Location()
    deltas = []

    loc.longitude = 0
    loc.solar_depression = "civil"

    for lat in range(MIN_LATITUDE-1, MAX_LATITUDE+2):
        loc.latitude = lat

        try:
            (start, end) = loc.daylight(date=date, local=False)
        except astral.AstralError as e:
            continue

        diff = (end - start).total_seconds() / 3600
        delta = abs(daylen - diff)
        deltas.append(delta)

        if (len(deltas) >= 3 and deltas[-2] < deltas[-1] and deltas[-2] < deltas[-3]):
            return lat - 1

def main():
    date = datetime.date(2016, 6, 21)
    img = Image.open(IMAGE_FN)
    last_lat = None
    daylen = 0

    while (daylen <= 24):
        lat = get_isoline_latitude(date, daylen)

        if (not lat or (lat and last_lat and abs(last_lat - lat) < MIN_SEPARATION_DEG)):
            daylen += 0.5
            continue

        color = \
            hsl_gradient(daylen, 0, 24, GRAD_START_COLOR, GRAD_END_COLOR)
        img = \
            outline_latitude(img, lat, string=str(daylen), color=color, font_size=40)
        print("outlined lat", lat, "daylen", daylen)
        last_lat = lat
        daylen += 0.5

    print_date(img, date, font_size=72)
    img.save("out.png")

main()
