from PIL import Image, ImageChops, ImageDraw, ImageFont
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline
plt.style.use('seaborn-white')
import json
import os
import math
import shutil
import io
from pprint import pprint
import csv
import imageio


class Common_Data(object):
    def __init__(self):
        self.diff_folder = None
        self.log_file = None
        self.max_diff = None

commons = Common_Data()

def process_image_pairs(a, b, identifier):
    # print (f"Identifier: {identifier}")
    # print (f"Image A: {a}")
    # print (f"Image B: {b}\n")
    if os.path.exists(a) and os.path.exists(b):
        make_difference_images(a, b, identifier)
    else:
        if not os.path.exists(a):
            print (f"\tCan't find A image - check {a} ")
        if not os.path.exists(b):
            print (f"\tCan't find B image - check {b} ")

def convert_dict(data):
    if isinstance(data, bytes):
        return data.decode()
    if isinstance(data, dict):   
        return dict(map(convert_dict, data.items()))
    if isinstance(data, tuple):  
        return tuple(map(convert_dict, data))
    if isinstance(data, list):   
        return list(map(convert_dict, data))
    return data

def flip_rgba_to_rgb(im, bg_colour=(255, 255, 255)):
    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode == 'RGBA':
        background = Image.new("RGB", im.size, (255, 255, 255))
        background.paste(im, mask=im.split()[3])
        return background
    else:
        return im

def normalise_images():
    commons.im1 = commons.im1.convert("RGB")
    commons.im2 = commons.im2.convert("RGB")
    if commons.im1.size != commons.im2.size:
        if verbose:
            print ("Resizing image B to size of image A")
        commons.im2 = commons.im2.resize(commons.im1.size)
        commons.image_rescaled = True
    else:
        commons.image_rescaled = False

def rmsdiff():
    """returns rmse (float) between two Image items"""

    try:
        diff = ImageChops.difference(commons.im1, commons.im2)
        h = diff.histogram()
        sq = (value*((idx%256)**2) for idx, value in enumerate(h))
        sum_of_squares = sum(sq)
        rms = math.sqrt(sum_of_squares/float(commons.im1.size[0] * commons.im1.size[1]))
        return rms

    except ValueError:
        print (commons.im1.size, commons.im1.getbands())
        print (commons.im2.size, commons.im2.getbands())
        print ("RMSE process failed. Check image modes are compatable")
        quit()

def make_before_after_gif():
    frames = []
    if os.path.exists(os.path.join(commons.diff_folder,"diff_masks")):
        imgs = [os.path.join(commons.diff_folder,"diff_masks", x) for x in  os.listdir(os.path.join(commons.diff_folder,"diff_masks"))]
        if commons.max_diff > 0:
            draw1 = ImageDraw.Draw(commons.im1)
            font = ImageFont.truetype("arial.ttf", 120)
            draw1.text((50, 90), f"  A", font=font,  fill=(255, 0, 0))
            frames.append(commons.im1)
            draw2 = ImageDraw.Draw(commons.im2)
            draw2.text((50, 90), f"  B", font=font,  fill = (0, 255, 255))
            frames.append(commons.im2)
            
            frames[0].save(os.path.join(commons.diff_folder, "flipper.gif"), format='GIF', append_images=frames[1:], save_all=True, duration=500, loop=0)

def put_a_and_b_image_in_results_folder():
    a_root = os.path.join(commons.diff_folder, "a")
    if not os.path.exists(a_root):
        os.makedirs(a_root)
    shutil.copy(a, a_root)

    b_root = os.path.join(commons.diff_folder, "b")
    if not os.path.exists(b_root):
        os.makedirs(b_root)
    shutil.copy(b, b_root)

def make_differance_and_diff_inverted_image():
    commons.difference = ImageChops.difference(commons.im1, commons.im2)
    commons.difference_inverted = ImageChops.invert(ImageChops.difference(commons.im1, commons.im2))
    
    commons.difference.save(os.path.join(commons.diff_folder, "diff_inverted.png"))
    commons.difference_inverted.save(os.path.join(commons.diff_folder, "diff.png"))

def make_histo(log_data, limits_profile=None):

    limits_profile=None

    bars_width = 0.5
    total_pixels = log_data["number of pixels"]
    commons.total_pixels = total_pixels
    width = log_data["height"]
    height = log_data["width"]
    image_rescaled = log_data["image_rescaled"]

    bins = [x for x in range(0, 256)]
    values = []
    for level in log_data["difference_masks"]:
        values.append(log_data["difference_masks"][level]['pixels in band'])

    percent_values  = [100/total_pixels * x for x in values]
    plt.bar(bins, percent_values, color='r', width=bars_width, alpha=0.7)

    # plt.yscale('symlog')

    if limits_profile:
        pixel_percent_limit = limits_profile[1]
        diff_depth_limit = len(limits_profile)    
        while len(limits_profile) != 256:
            limits_profile.append(0)
  
        bins_new = np.linspace(min(bins), max(bins), 300) 
        my_spline = make_interp_spline(bins, limits_profile, k=3)
        pixel_percent_boundaries_smooth = my_spline(bins_new)

        plt.plot(bins_new, pixel_percent_boundaries_smooth, color='g', linestyle=" ")
        plt.fill_between(bins_new, pixel_percent_boundaries_smooth, color='g', alpha=0.4)

    plt.title("Pixel difference profile")
    plt.ylabel("Percent of pixels changed at given difference depth")
    plt.xlabel("Difference depth (8-bit step increments)")
    plt.xticks(np.arange(0, 256, 32))


    if int(max(percent_values))+5 < 100:
        plt.ylim([0, int(max(percent_values))+5])
        y = int(max(percent_values))
    else:
        plt.ylim([0, 100])
        y = 95

    x = 100/commons.max_diff*30
    step_size = 1.5

    # plt.text(x,y, f'Key Data', fontsize = 12)
    # plt.text(x, y-step_size*1, f'Identifier: {identifier}', fontsize = 8)
    # plt.text(x, y-step_size*2, f'Image Resolution: {width}w x {height}h', fontsize = 8)
    # plt.text(x, y-step_size*3, f'Total Pixels: {total_pixels}', fontsize = 8)
    # plt.text(x, y-step_size*4, f'B image rescaled?: {image_rescaled}', fontsize = 8)
    # plt.text(x, y-step_size*5, f'Max Difference Size: {commons.max_diff}', fontsize = 8)
    # plt.text(x, y-step_size*6, f'Percent Pixels Unchanged: {percent_values[0]:.2f}%', fontsize = 8)
    # plt.text(x, y-step_size*7, f'RMSe: {commons.rmse:.3f}', fontsize = 8)
    # if limits_profile:
    #     plt.text(x, y-step_size*9, f'Profile Reference:', fontsize = 8, color='g')
    #     plt.text(x, y-step_size*10, f'  {commons.limits_reference}', fontsize = 8, color='g')

    plt.xlim([-1, commons.max_diff])
    plt.savefig(os.path.join( commons.diff_folder,"zoomed_chart.png"), dpi=300)

    plt.bar(bins, percent_values, color='r', width=bars_width, alpha=0.7)
    plt.title("Pixel difference profile")
    plt.ylabel("Percent of pixels changed at given difference depth")
    plt.xlabel("Difference depth (8-bit step increments)")
    plt.xticks(np.arange(0, 256, 32))

    if limits_profile:
        plt.plot(bins_new, pixel_percent_boundaries_smooth, color='g')
        plt.fill_between(bins_new, pixel_percent_boundaries_smooth, color='g', alpha=0.4)

    x = 125
    y = 85
    step_size = 4
    
    # plt.text(x,y, f'Key Data', fontsize = 12)
    # plt.text(x, y-step_size*1, f'Identifier: {identifier}', fontsize = 8)
    # plt.text(x, y-step_size*2, f'Image Resolution: {width}w x {height}h', fontsize = 8)
    # plt.text(x, y-step_size*3, f'Total Pixels: {total_pixels}', fontsize = 8)
    # plt.text(x, y-step_size*4, f'B image rescaled?: {image_rescaled}', fontsize = 8)
    # plt.text(x, y-step_size*5, f'Max Difference Size: {commons.max_diff}', fontsize = 8)
    # plt.text(x, y-step_size*6, f'Percent Pixels Unchanged: {percent_values[0]:.2f}%', fontsize = 8)
    # plt.text(x, y-step_size*7, f'RMSe: {commons.rmse:.3f}', fontsize = 8)
    # if limits_profile:
    #     plt.text(x, y-step_size*9, f'Profile Reference:', fontsize = 8, color='g')
    #     plt.text(x, y-step_size*10, f'  {commons.limits_reference}', fontsize = 8, color='g')

    plt.ylim([0.0, 100])
    plt.xlim([-1, 256])
    plt.savefig(os.path.join( commons.diff_folder,"full_chart.png"), dpi=300)
    plt.close()


def make_composite_difference_mask(diff_img):
    
    """"""
    diff_img.save(os.path.join(commons.diff_folder,"composite_diff_mask.png"))

def make_difference_levels_gif():
    frames = []
    if os.path.exists(os.path.join(commons.diff_folder,"diff_masks")):
        imgs = [os.path.join(commons.diff_folder,"diff_masks", x) for x in  os.listdir(os.path.join(commons.diff_folder,"diff_masks"))]
        if commons.max_diff > 0:
            for counter, i in enumerate(imgs, 1):
                new_frame = Image.open(i)
                draw = ImageDraw.Draw(new_frame)
                font = ImageFont.truetype("arial.ttf", 30)
                draw.text((50, 90), f"diff depth: {counter}", font=font)
                new_frame = new_frame.convert('P') 
                frames.append(new_frame)
            frames[0].save(os.path.join(commons.diff_folder, "diff.gif"), format='GIF', append_images=frames[1:], save_all=True, duration=100, loop=0)

def make_difference_images(a, b, identifier=False, quickmode=False):
    """If there is a non-zero RMSe value, a difference image (and its inverse) is created.
    This is useful as a visual indicator
     for what the actual difference is. 
    The bi-tonal images are a threshold-ed representation of the diff starting at diff distance 1
    This is useful to see where the diff is in real terms - consider it an exaggeration of the diff we can see.  
    """
    # debug = True
    commons.im1, commons.im2 = Image.open(a), Image.open(b)
    
    if not quickmode:
        a_input = commons.im1.info
        a_input["bands"] = commons.im1.getbands()

        b_input = commons.im2.info
        b_input["bands"] = commons.im2.getbands()

    normalise_images()

    rmse = rmsdiff()
    commons.rmse = rmse
    log_data = {"a":{"source":a.replace("\\", "/")}, "b":{"source":b.replace("\\", "/")}, "difference_masks":{}}
    width, height = commons.im1.size
    number_of_pixels = width * height 
    log_data["number of pixels"] = number_of_pixels
    log_data["width"] = width
    log_data["height"] = height
    log_data['image_rescaled'] = commons.image_rescaled

    
    a_final = commons.im1.info
    a_final["bands"] = commons.im1.getbands()
    b_final = commons.im2.info
    b_final["bands"] = commons.im2.getbands()

    log_data["RMSE"] = rmse

    if "icc_profile" in a_input:
        del a_input['icc_profile']
    if "icc_profile" in a_final:
        del a_final['icc_profile']

    if "exif" in a_input:
        del a_input['exif']
    if "exif" in a_final:
        del a_final['exif']

    if "photoshop" in a_input:
        del a_input['photoshop']
    if "photoshop" in a_final:
        del a_final['photoshop']



    if "icc_profile" in b_input:
        del b_input['icc_profile']
    if "icc_profile" in b_final:
        del b_final['icc_profile']


    if "exif" in b_input:
        del b_input['exif']
    if "exif" in b_final:
        del b_final['exif']


    if "photoshop" in b_input:
        del b_input['photoshop']
    if "photoshop" in b_final:
        del b_final['photoshop']


    log_data['a']['input_image'] = convert_dict(a_input)
    log_data['a']["bytes"] = os.stat(a).st_size
    log_data['a']["size"] = {}
    log_data['a']["size"]["width"], log_data['a']["size"]["height"] = commons.im1.size
    if a_input != a_final:
        log_data['a']['comparision_image'] = convert_dict(a_final)
        log_data['a']['conversion note'] = "Image was converted to an RGB image, so some measures are relative to this conversion, not the orignal image"
        
    log_data['b']['input_image'] = convert_dict(b_input)
    log_data['b']["bytes"] = os.stat(b).st_size
    log_data['b']["size"] = {}
    log_data['b']["size"]["width"], log_data['b']["size"]["height"] = commons.im2.size
    if b_input != b_final:
        log_data['b']['comparision_image'] = convert_dict(b_final)
        log_data['b']['conversion note'] = "Image was converted to an RGB image, so some measures are relative to this conversion, not the orignal image"
        
    # print (f"RMSE: {rmse}")
    
    commons.diff_folder = os.path.join( destination_folder, identifier)
    if not os.path.exists(commons.diff_folder):
        os.makedirs(commons.diff_folder)

    commons.log_file = os.path.join(commons.diff_folder, identifier+".json")

    # put_a_and_b_image_in_results_folder()
    # make_differance_and_diff_inverted_image()

    diff_folder = os.path.join( destination_folder, identifier) 
    commons.difference = ImageChops.difference(commons.im1, commons.im2)

    pixels_a = commons.im1.load()
    pixels_b = commons.im2.load()
    width, height = commons.im1.size

    pixels = list(commons.difference.convert('L').getdata())
    pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]
    my_histo = {}
    for row in pixels:
        for pixel in row:
            if pixel not in my_histo:
                my_histo[pixel] = 0
            my_histo[pixel] += 1

    commons.max_diff = max(list(my_histo.keys()))
    # print (f"Max diff depth: {commons.max_diff}")
    log_data["Number of difference levels"] = commons.max_diff

    for thresh in range (255, -1, -1):
        fn = lambda x : 255 if x > thresh else 0
        counter = 255-thresh
        counter_string = str(counter).zfill(3)

        # if counter < commons.max_diff+2 and counter != 0:
            
        #     if not os.path.exists(os.path.join(commons.diff_folder,"diff_masks")):
        #         os.makedirs(os.path.join(commons.diff_folder,"diff_masks"))
        #     fname = f"bilevel_{counter_string}.png"
        #     diff_img = commons.difference_inverted.convert('L').point(fn, mode='1')
        #     diff_img.save(os.path.join(commons.diff_folder,"diff_masks", fname))

        #     if counter == 1:
        #         make_composite_difference_mask(diff_img)
        
        log_data["difference_masks"][counter] = {}

        if counter in my_histo:
            log_data["difference_masks"][counter]["pixels in band"] = my_histo[counter]
        else:
            log_data["difference_masks"][counter]["pixels in band"] = 0        
        
    # make_difference_levels_gif()
    # make_before_after_gif()

    # limits = {"limits_profile":[30, 30, 25, 15, 5, 2, 1, 0], "limits_reference":"Test Access Copy Profile"}
    
    # commons.limits_profile = limits["limits_profile"]
    # commons.limits_reference = limits["limits_reference"]

    # make_histo(log_data, commons.limits_profile)
    make_histo(log_data)

    # print (f"\nSee:\n\n\t{commons.diff_folder}\n")
    with open(commons.log_file, "w") as outfile:
        outfile.write(json.dumps(log_data, indent=4, sort_keys=True))

    commons.log_data = log_data

def make_chart_gif(trigger_fname=""):
    images = []
    files = os.listdir(destination_folder)
    files.sort()
    files = files[::-1]
    for root in files:
        images.append(imageio.imread(os.path.join(destination_folder,root, trigger_fname)))

    imageio.mimsave(os.path.join(dest, trigger_fname.replace(".png", "")+".gif"), images)


# a = r"E:\ipres_poster_image_stuff\bulk_images\test\slow_transfer_28_july.png"
# dest = r"E:\ipres_poster_image_stuff\bulk_images\image_comparision_outputs\jpg_test_1"
# log_file_name = "slow_transfer_28_july_png.csv"


a = r"E:\ipres_poster_image_stuff\bulk_images\test\WHA-17_pm.tif"
dest = r"E:\ipres_poster_image_stuff\bulk_images\image_comparision_outputs\jpg_test_2"
source = "WHA-17_pm.tif"


# a = r"E:\ipres_poster_image_stuff\bulk_images\test\LaDeDas_RnR Sandwich.tif"
# dest = r"E:\ipres_poster_image_stuff\bulk_images\image_comparision_outputs\jpg_test_3"
# log_file_name = "LaDeDas_RnR Sandwich_tif.csv"


# a = r"E:\ipres_poster_image_stuff\bulk_images\test\AWC-0247-F_34.jpg"
# dest = r"E:\ipres_poster_image_stuff\bulk_images\image_comparision_outputs\jpg_test_4"
# log_file_name = "AWC-0247-F_34_jpg.csv"


# a = r"E:\ipres_poster_image_stuff\bulk_images\test\1@@2-215440.tif"
# dest = r"E:\ipres_poster_image_stuff\bulk_images\image_comparision_outputs\jpg_test_5"
# log_file_name = "1@@2-215440_tif.csv"



log_file_name = source.replace(".", "_")+".csv"
destination_folder = os.path.join(dest, "files")
if not os.path.exists(dest):
    os.makedirs(dest)
logr = [["source", "type", "reference", "rmse", "max diff", "change score", "pixels in image"]]
base_img = Image.open(a)
rgb_im = base_img.convert('RGB')
for i in range(100, -1, -1):
    identifier  = str(i).zfill(3)
    my_f = os.path.join(dest, identifier+".jpg") 
    rgb_im.save(my_f, quality=i)
    process_image_pairs(a, my_f, identifier)
    commons.change_score = 0
    for band in commons.log_data["difference_masks"]:
        commons.number_of_pixels = commons.log_data["difference_masks"][band]["pixels in band"] 
        change_contrbution = int(band)*int(commons.number_of_pixels)
        commons.change_score += change_contrbution

    row = [ source, "jpg", i, commons.rmse, commons.change_score, commons.max_diff, commons.total_pixels]
    logr.append(row)
    print (row)
    os.remove(my_f)

with open(os.path.join(dest , log_file_name), "w", newline= "") as data:
    writer = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerows(logr)

make_chart_gif("full_chart.png")
make_chart_gif("zoomed_chart.png")