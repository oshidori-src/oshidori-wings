#
# Copyright 2019 Oshidori LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Palette generator"""


# Dependencies import
from PIL import Image, ImageDraw, ImageColor
from colorsys import rgb_to_hls, hls_to_rgb
import json
import traceback
import sys


def adjust_lum(color, lum):
    """
    Assign new luminosity into provided color

    :param color: A color string
    :param lum: A luminosity value
    :return: (red, green, blue)
    """
    # Convert color to HLS
    r, g, b = ImageColor.getrgb(color)
    h, l, s = rgb_to_hls(r, g, b)

    # Convert new color back into RGB
    r, g, b = hls_to_rgb(h, float(lum), s)

    # Return adjusted color as RGB triad
    return int(r), int(g), int(b)


def get_text_size(text):
    """
    Calculate text size, based on the provided text

    :param text: Text represented as a string
    :return: (width, height)
    """

    # Create a temporary canvas, just to do text size calculation
    im = Image.new('RGBA', (0, 0), (0, 0, 0, 255))
    draw = ImageDraw.Draw(im)

    # Get text size based on default font and one symbol
    return draw.textsize(text)


def calc_canvas_size(palette_dict, rectangle_size, padding, extended=False):
    """
    Calculate canvas size based on palette size

    :param palette_dict: Used palette, represented as a dictionary
    :param rectangle_size: The size of the color rectangle
    :param padding: Global padding
    :param extended: True, if this palette is extended
    :return: (width, height)
    """
    # Find the longest color name
    longest_color_name = ""
    for color_dict in palette_dict['palette']:
        if len(color_dict["name"]) > len(longest_color_name):
            longest_color_name = color_dict["name"]

    # Get longest color name size
    longest_color_name_width, longest_color_name_height = get_text_size(longest_color_name)

    if extended:
        # Get text size for the palette name
        palette_name_width, palette_name_height = get_text_size(
            palette_dict['name'] + " " + palette_dict['version'] + " (extended)"
        )

        # Set max canvas width, based on the palette name line
        max_canvas_width = padding + palette_name_width + padding

        # Calculate color line length - this will be the tricky one for the extended palette:
        # We have padding first and then there are three colors stacks that contain 6 color variation each
        # These color variations have a size of (padding + 2) pixels
        color_line_length = padding + 3 * 6 * (padding + 2)

        # Also on the same line - there is a regular color rectangle, five parts of the padding and color name
        color_line_length += 3 * padding + rectangle_size + padding + longest_color_name_width + padding

    else:
        # Get text size for the palette name
        palette_name_width, palette_name_height = get_text_size(
            palette_dict['name'] + " " + palette_dict['version']
        )

        # Set max canvas width, based on the palette name line
        max_canvas_width = padding + palette_name_width + padding

        # Color line length for the non-extended palette
        color_line_length = padding + rectangle_size + padding + longest_color_name_width + padding

    # Check if the color line is longer than max canvas width
    if color_line_length > max_canvas_width:
        max_canvas_width = color_line_length

    # Calculate canvas height
    canvas_height = padding + longest_color_name_height + (
        padding + rectangle_size
    ) * len(palette_dict['palette']) + padding

    return max_canvas_width, canvas_height


def main():
    """
    Entry point for the generator
    """

    try:
        print('~ Palette generation in progress ~')

        # Open palette file and load it into the dictionary
        with open('src/palette.json') as palette_file:
            palette_dict = json.load(palette_file)

        # Define main variables for the generator
        padding = 5
        lum_step = 20
        rectangle_size = 10
        text_width, text_height = get_text_size(" ")

        print('~ Draw palette ~')

        # Create canvas
        im = Image.new('RGBA', calc_canvas_size(palette_dict, rectangle_size, padding), (0, 0, 0, 255))
        draw = ImageDraw.Draw(im)

        # Draw the name of the palette
        draw.text(
            (padding, padding),
            palette_dict['name'] + " " + palette_dict['version'],
            fill=(255, 255, 255, 255)
        )

        # Set initial coordinates for the palette colors
        x = padding
        y = padding + text_height + padding

        # Draw palette colors
        for color_dict in palette_dict['palette']:
            # Draw color rectangle
            draw.rectangle(
                [x, y, x + rectangle_size, y + rectangle_size],
                fill=color_dict['color']
            )

            # Draw color name
            draw.text(
                (x + rectangle_size + padding, y),
                color_dict['name'],
                fill=color_dict['color']
            )

            # Shift y coordinate of the next color rectangle
            y += rectangle_size + padding

        # Cleanup palette from excessive colors
        # Note: The generator uses white and black colors for background and palette name
        # that's why there would be len(palette_dict['palette']) plus two colors in palette
        im = im.convert('P', palette=Image.ADAPTIVE, colors=len(palette_dict['palette']) + 2)

        # Save palette into the file
        im.save('dist/' + palette_dict['name'] + '.png')

        print('~ Draw extended palette ~')

        # Create canvas
        im = Image.new('RGBA', calc_canvas_size(palette_dict, rectangle_size, padding, extended=True), (0, 0, 0, 255))
        draw = ImageDraw.Draw(im)

        # Draw the name of the palette
        draw.text(
            (padding, padding),
            palette_dict['name'] + " " + palette_dict['version'] + " (extended)",
            fill=(255, 255, 255, 255)
        )

        # Set initial coordinates for the palette colors
        y = padding + text_height + padding

        # Draw palette colors
        for color_dict in palette_dict['palette']:
            # Reset x coordinate
            x = padding

            # For each color stacks in [dark, normal blend, bright]
            for initial_lum in [30, 90, 150]:
                for step in range(1, 7):
                    draw.rectangle(
                        [
                            x, y,
                            x + padding, y + rectangle_size
                        ],
                        fill=adjust_lum(color_dict['color'], initial_lum + lum_step * step)
                    )
                    x += padding + 2

                # Make some space between stacks
                x += padding

            # Draw original color for reference
            draw.rectangle(
                [x, y, x + rectangle_size, y + rectangle_size],
                fill=color_dict['color']
            )

            # Draw color name
            draw.text(
                (x + rectangle_size + padding, y),
                color_dict['name'],
                fill=color_dict['color']
            )

            # Shift y coordinate of the next color rectangle
            y += rectangle_size + padding

        # Save palette into the file
        im.save('dist/' + palette_dict['name'] + '_ext.png')

        print('~ Palette files was generated successfully ~')
        print('~ You can find it in:')
        print('  * `dist/' + palette_dict['name'] + '.png`')
        print('  * `dist/' + palette_dict['name'] + '_ext.png`')

    except Exception:
        print("~ Can't generate the palette: \n{0}".format(traceback.format_exc()))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
