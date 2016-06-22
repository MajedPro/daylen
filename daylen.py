#!/usr/bin/env python3

import astral

import colorsys
import sys

from PIL import Image, ImageDraw, ImageFont

DEGREE_TO_PX = 12.84
IMAGE_FN = "azmap.png"
FONT_FN = "/usr/share/fonts/TTF/calibri.ttf"

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
    
    # Create mask + composite images
    
    ell_layer = \
        Image.new(img.mode, img.size, color=color)    
    mask = Image.new("L", img.size)
    mask_dc = ImageDraw.Draw(mask)
    half_t = thickness / 2
    font = ImageFont.truetype(FONT_FN, font_size)
    (text_w, text_h) = font.getsize(string)
    
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
    
    """ Return a position on a HSL gradient. RGB tuples have values in the
    range [0 .. 255].
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

def outline_latitudes_for_date(*args):
    img = Image.open(IMAGE_FN)
    
    for lat in range(35, 90, 5):
        loc = astral.Location()
        loc.latitude = lat
        loc.longitude = 0
        loc.solar_depression = "civil"
        diff = 0
        
        try:
            sun = loc.sun()
            diff = (sun["dusk"] - sun["dawn"]).total_seconds() / 3600
            diff_str = "{:.1f}".format(diff)
            
            print("latitude {}: dawn {}, sunrise {}, sunset {}, dusk {}, diff {}"
                .format(lat, sun["dawn"], sun["sunrise"], sun["sunset"], sun["dusk"], diff_str))
            
            color = \
                hsl_gradient(diff, 0, 24, (160, 0, 0), (0, 160, 0))
            img = \
                outline_latitude(img, lat, string=diff_str, color=color, font_size=40)
        except astral.AstralError as e:
            prerr("Cannot get times for latitude {}: {}".format(lat, e))
    
    #debug_hsl_gradient(img, 0, 24, (160, 0, 0), (0, 160, 0))
    img.save("out.png")    
    

def main():
    
    outline_latitudes_for_date(2016, 6, 21)
    

    
    


main()
