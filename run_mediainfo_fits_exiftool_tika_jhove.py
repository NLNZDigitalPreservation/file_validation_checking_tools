import subprocess
import os

testSet_root = r"TestSet"

def call_subprocess(cmd):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if err:
        print (err)

def setup():
    if not os.path.exists("logs/tika"):
        os.makedirs("logs/tika")
    if not os.path.exists("logs/media_info"):
        os.makedirs("logs/media_info")
    if not os.path.exists("logs/exiftool"):
        os.makedirs("logs/exiftool")
    if not os.path.exists("logs/jhove"):
        os.makedirs("logs/jhove")
setup()

def get_files():
    my_files = []
    for folder in [x for x in os.listdir(testSet_root) if os.path.isdir(os.path.join(testSet_root, x))]:
        for f in [x for x in os.listdir(os.path.join(testSet_root, folder)) if os.path.isfile(os.path.join(testSet_root, folder, x))]:
            my_files.append(os.path.join(testSet_root, folder, f))
    return my_files
        
def do_tika(f, outfile):
    outfile = os.path.join("logs", "tika", outfile+".xml") 
    cmd = f"java -jar E:/tools/tika/tika-app-1.7.jar -x -m {f} > {outfile}"
    if not os.path.exists(outfile):
        print (f"doing {outfile}" )
        call_subprocess(cmd)

def do_jhove(f, outfile):
   outfile = os.path.join("logs", "jhove", outfile+".xml") 
    """Calls JHOVE for both images and traps the results
    Will fail if jhove isn't on the host system - TODO (clean up jhove fail)"""

    __, format = f.rsplit(".", 1)
    if format == "tif":
        format = "TIFF"
    if format == "tiff":
        format = "TIFF"
    module_lookup = {
                "AIFF":" -m aiff-hul ",
                "ASCII":" -m ascii-hul ",
                "BYTESTREAM":" -m bytestream=hul ",
                "GIF":" -m gif-hul ",
                "HTML":" -m html-hul ",
                "JPEG":" -m jpeg-hul ",
                "JPEG2000":" -m jpeg2000-hul ",
                "PDF":" -m pdf-hul ",
                "TIFF":" -m tiff-hul ",
                "UTF8":" -m utf8-hul ",
                "WAV":" -m wave-hul ",
                "XML":" -m xml-hul "}

    if format not in module_lookup:
        print ("format", format, "not in lookup for JHOVE - fix this here")
    module = module_lookup[format]
    cmd = f'''jhove {module} "{f}" > "{outfile}"'''
    subprocess.call(cmd, shell=True)

def do_mediainfo(f, outfile):
    outfile = os.path.join("logs", "media_info", outfile+".json") 
    cmd = f"E:\\tools\\mediainfo_cli\\MediaInfo_cli.exe --Output=JSON {f} > {outfile}"
    if not os.path.exists(outfile):
        call_subprocess(cmd)


def do_exiftool(f, outfile):
    outfile = os.path.join("logs", "exiftool", outfile+".json") 
    cmd = f"exiftool -json {f} > {outfile}"
    if not os.path.exists(outfile):
        call_subprocess(cmd)

def do_fits(f, outfile):
    outfile = os.path.join("E:\\format_analysis\\running_characterisers", "logs", "fits", outfile) 
    if not os.path.exists(outfile+".xml"):
        temp_file = get_file(f)
        print (f"Processing {temp_file}")
        cmd = f"E:\\tools\\FITS\\fits-1.5.0\\fits -i {temp_file} > {outfile}.xml"
        call_subprocess(cmd)
        os.remove(temp_file)
    else:
        print (f"Skipping {f} - done")


testSet = get_files()

for f in testSet:
    print (f)
    __, outfile = f.rsplit(os.sep, 1)
    outfile, __ = outfile.rsplit(".", 1)
    do_mediainfo(f, outfile)
    do_exiftool(f, outfile)
    do_tika(f, outfile)
    do_fits(f, outfile)

