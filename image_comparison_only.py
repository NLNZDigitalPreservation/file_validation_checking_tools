from PIL import Image, ImageChops, ImageDraw, ImageFont
import os
import math


def process_folder(a_root, b_root):
    for f in os.listdir(a_root):
        a = os.path.join(a_root, f)
        b = os.path.join(b_root, f)
        identifier, __ = f.rsplit(".", 1)
        if os.path.exists(a) and os.path.exists(b):
            make_difference_images(a, b, identifier)

def rmsdiff(im1, im2):
    """returns rmse (float) between two Image items"""
    diff = ImageChops.difference(im1, im2)
    h = diff.histogram()
    sq = (value*((idx%256)**2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares/float(im1.size[0] * im1.size[1]))
    return rms


def make_difference_images(a, b, identifier=False):
    """If there is a none zero RMSe value, a difference image (and its inverse) is created.
    This is useful as visual indicator for what the actaul difference is. 
    THe biatonal image are a thresholded representation of the diff, with the theshold set at max_level - 1, 2, 3, 4 and 5 respectively
    This is useful to see where the diff is in real terms - consider it an exaggeration of the diff we can see.  
    """
    debug = False
    im1, im2 = Image.open(a), Image.open(b)

    rmse = rmsdiff(im1, im2)

    print (identifier, rmse)

    if rmse != 0:

        if identifier:
            diff_folder = os.path.join( destination_folder, identifier) 
        else:
            diff_folder = os.path.join( destination_folder) 
        if not os.path.exists(diff_folder):
            os.makedirs(diff_folder)

        difference = ImageChops.difference(im1, im2)
        difference.save(os.path.join(diff_folder, "diff_inverted.png"))
        difference = ImageChops.invert(difference)
        difference.save(os.path.join(diff_folder, "diff.png"))

        pixels_a = im1.load()
        pixels_b = im2.load()
        max_diff = 0
        width, height = im1.size
        for x in range(width):
            for y in range(height):

                a_r, a_g, a_b = pixels_a[x, y]
                b_r, b_g, b_b = pixels_b[x, y]

                r_max, g_max, b_max  = max(a_r, b_r), max(a_g, b_g),  max(a_b, b_b)
                r_min, g_min, b_min  = min(a_r, b_r), min(a_g, b_g),  min(a_b, b_b)
                r_diff, g_diff, b_diff = r_max-r_min,  g_max-g_min,  b_max-b_min,  

                pix_max = max(r_diff, g_diff, b_diff)

                if pix_max > max_diff:
                    max_diff = pix_max
                    if debug:
                        print (max_diff, pix_max, "|", y, x, "|", a_r, a_g, a_b, "|", b_r, b_g, b_b , "|",  r_max, g_max, b_max,  "|", r_min, g_min, b_min,  "|", r_diff, g_diff, b_diff )
        if verbose:
            print (f"\tMax diff value found of: {max_diff}")
        for thresh in range (255, 255-max_diff, -1):
            fn = lambda x : 255 if x > thresh else 0
            counter = str(255-thresh).zfill(3)
            if counter != "000":
                if not os.path.exists(os.path.join(diff_folder,"diff_masks")):
                    os.makedirs(os.path.join(diff_folder,"diff_masks"))
                fname = f"bilevel_{counter}.png"
                diff_img = difference.convert('L').point(fn, mode='1')
                diff_img.save(os.path.join(diff_folder,"diff_masks", fname))


                ###do comp mask
                if counter == "001":
                    diff_img.save(os.path.join(diff_folder,"composite_diff_mask.png"))
   

        ### do gifs
        frames = []
        if os.path.exists(os.path.join(diff_folder,"diff_masks")):
            imgs = [os.path.join(diff_folder,"diff_masks", x) for x in  os.listdir(os.path.join(diff_folder,"diff_masks"))]
            if max_diff > 0:
                for counter, i in enumerate(imgs, 1):
                    new_frame = Image.open(i)
                    draw = ImageDraw.Draw(new_frame)
                    font = ImageFont.truetype("arial.ttf", 30)
                    draw.text((50, 90), f"diff mask: {counter}", font=font)
                    new_frame = new_frame.convert('P') 
                    frames.append(new_frame)
                frames[0].save(os.path.join(diff_folder, "diff.gif"), format='GIF', append_images=frames[1:], save_all=True, duration=100, loop=0)

        ### do flipper gifs
        frames = []
        if os.path.exists(os.path.join(diff_folder,"diff_masks")):
            imgs = [os.path.join(diff_folder,"diff_masks", x) for x in  os.listdir(os.path.join(diff_folder,"diff_masks"))]
            if max_diff > 0:
                draw1 = ImageDraw.Draw(im1)
                font = ImageFont.truetype("arial.ttf", 120)
                draw1.text((50, 90), f"ORIGINAL", font=font,  fill = (255, 0, 0))
                frames.append(im1)
                draw2 = ImageDraw.Draw(im2)
                draw2.text((50, 90), f"TREATED", font=font,  fill = (0, 255, 255))
                frames.append(im2)
                
                frames[0].save(os.path.join(diff_folder, "flipper.gif"), format='GIF', append_images=frames[1:], save_all=True, duration=500, loop=0)


verbose = True
a_root = r"E:\completed\fmt_488_1\FL66121194\publication-1_pdf\pages_as_images\original"
b_root = r"E:\completed\fmt_488_1\FL66121194\publication-1_pdf\pages_as_images\new"
destination_folder = r"E:\tools\file_validation_checking_tools\image_temp_comparisions"




process_folder(a_root, b_root)
