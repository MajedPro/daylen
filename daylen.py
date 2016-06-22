#!/usr/bin/env python3

import colorsys
import datetime
import functools
import math
import sys

import astral

from PIL import Image, ImageDraw, ImageFont

IMAGE_FN = "map.png"
FONT_FN = "/usr/share/fonts/TTF/calibri.ttf"

MAP_CENTER_X = 998
MAP_CENTER_Y = 293
DEGREE_TO_PX = 13.35
MIN_LATITUDE = 25
MAX_LATITUDE = 90

MIN_SEPARATION_DEG = 2.5
GRAD_START_COLOR = (160, 0, 0)
GRAD_END_COLOR = (0, 160, 0)

DEBUG = False



# Main pipeline

def apply_isolines_to_image(img, date):
    daylen = 0
    daylen_incr = 0.5
    last_lat = None

    # If summer, start iterating from isoline 24 to ensure the polar day
    # region is marked. Same in winter for polar night.

    if (is_summer(date)):
        daylen = 24
        daylen_incr = -daylen_incr

    # Loop over isolines and apply to image if the separation between isolines
    # is sufficient and latitudes are not extremely polar.

    while (daylen <= 24 and daylen >= 0):
        lat = get_isoline_latitude(date, daylen)

        if (not lat or (lat and
            (last_lat and abs(last_lat - lat) < MIN_SEPARATION_DEG) or (lat > 85)
        )):
            daylen += daylen_incr
            continue

        color = \
            get_hsl_gradient_point(daylen, 0, 24, GRAD_START_COLOR, GRAD_END_COLOR)
        img = \
            outline_latitude(img, lat, string=str(daylen), color=color, font_size=40)

        prerr("{}: Applied isoline {} at latitude {:.2f}".format(date, daylen, lat))
        last_lat = lat
        daylen += daylen_incr

    print_date(img, date, font_size=72)
    return img

def get_isoline_latitude(date, daylen):

    """ Run a binary search for day length isoline latitude. Uses a
    convergence guard to work around shortcomings of the astral module:
    extremely short or long day isolines in polar regions will cause
    recursion errors otherwise. In summer, high isoline values correspond to
    high latitudes; the reverse in winter.
    """

    precision = 0.001
    summer = is_summer(date)
    convergence = []

    def binsearch_latitude(low_lat, high_lat, target_dl):
        mid_lat = low_lat + (high_lat - low_lat) / 2

        low_dl = get_daylen_on_latitude(date, low_lat)
        mid_dl = get_daylen_on_latitude(date, mid_lat)
        high_dl = get_daylen_on_latitude(date, high_lat)

        convergence.append(mid_lat)

        if (summer and (low_dl > target_dl)):
            return None
        elif (not summer and (low_dl < target_dl)):
            return None

        if (
            len(convergence) >= 3
            and abs(convergence[-1] - convergence[-2]) <= precision
            and abs(convergence[-2] - convergence[-3]) <= precision
        ):
            return mid_lat

        if (abs(low_dl - target_dl) <= precision):
            return low_lat
        elif (abs(mid_dl - target_dl) <= precision):
            return mid_lat
        elif (abs(high_dl - target_dl) <= precision):
            return high_lat

        if (summer and low_dl <= target_dl and target_dl < mid_dl):
            return binsearch_latitude(low_lat, mid_lat, target_dl)
        elif (not summer and low_dl >= target_dl and target_dl > mid_dl):
            return binsearch_latitude(low_lat, mid_lat, target_dl)
        else:
            return binsearch_latitude(mid_lat, high_lat, target_dl)

    return binsearch_latitude(MIN_LATITUDE, MAX_LATITUDE, daylen)

@functools.lru_cache(maxsize=2048)
def get_daylen_on_latitude(date, lat):

    """ Memoized latitude to day length function, returns day length in hours. """

    loc = astral.Location()

    loc.latitude = lat
    loc.longitude = 0
    loc.solar_depression = "civil"

    try:
        (start, end) = loc.daylight(date=date, local=False)
    except astral.AstralError as e:
        if (is_summer(date)):
            return math.inf
        return -math.inf

    return (end - start).total_seconds() / 3600

def outline_latitude(img, latitude, string="", font_size=20, thickness=3, color=(200, 0, 0)):

    """ Outline a latitude with a circle of given thickness and color. Uses
    a mask layer to overcome the lack of a thickness option in PIL's ellipse
    method.
    """

    r = (90 - latitude) * DEGREE_TO_PX
    center_x = MAP_CENTER_X
    center_y = MAP_CENTER_Y

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

# Auxiliary routines

def prerr(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def get_hsl_gradient_point(val, min_val, max_val, start_rgb, end_rgb):

    """ Return an RGB position on a HSL gradient. RGB tuples have values in
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

def print_date(img, date, font_size=40, padding=10):

    """ Print the date into the upper left corner of image. """

    dc = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_FN, font_size)
    date_str = date.strftime("%b\n%d")

    dc.text((padding, padding), date_str, font=font, fill=(20, 20, 20))

def is_summer(date):
    loc = astral.Location()
    loc.longitude = 0

    loc.latitude = 60
    north_rise = loc.sunrise(date=date)
    loc.latitude = 30
    south_rise = loc.sunrise(date=date)

    return north_rise < south_rise

# Debugging routines

def debug_hsl_gradient(img, *extra):
    min_val = extra[0]
    max_val = extra[1]
    dim = 50
    dc = ImageDraw.Draw(img)

    for i in range(min_val, max_val + 1):
        color = get_hsl_gradient_point(i, *extra)
        pos = i - min_val
        dc.rectangle([0 + pos*dim, 0, 0 + pos*dim + dim, dim], fill=color)

def debug_latitudes(img):
    start = None

    for i in range(MIN_LATITUDE, MIN_LATITUDE+5):
        if (i % 5 == 0):
            start = i
            break

    for lat in range(start, MAX_LATITUDE, 5):
        img = outline_latitude(img, lat, str(lat))

    return img

# Entry point

def main():
    date = datetime.date(2016, 6, 1)
    img = Image.open(IMAGE_FN)

    if (not DEBUG):
        img = apply_isolines_to_image(img, date)
    else:
        img = debug_latitudes(img)

    img.save("out.png")

main()
