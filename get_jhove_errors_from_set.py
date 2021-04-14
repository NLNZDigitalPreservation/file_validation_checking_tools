import os
import subprocess
import shutil


def do_jhove(f, dest):
    """Calls JHOVE for both images and traps the results
    Will fail if jhove isn't on the host system - TODO (clean up jhove fail)"""

    __, format = f.rsplit(".", 1)
    if format == "tif":
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
    cmd = f'''jhove {module} "{f}" > "{dest}"'''
    subprocess.call(cmd, shell=True)

def get_files_list(root):
    files = []
    for folder in os.listdir(root):
        for f in os.listdir(os.path.join(root, folder)):
            files.append([os.path.join(root, folder, f), f])
    return files

def do_summary(folder):

    jhoves = r"\\wlgprdfile12\home$\Wellington\GattusoJ\HomeData\Desktop\clean_up_part_2\temp_jhove_reports"

    files = get_files_list(folder)

    if flush:
        shutil.rmtree(jhoves)
        os.makedirs(jhoves)

        for f in files:
            fpath, fname = f
            dest = os.path.join(jhoves, fname.replace(".tif", ".txt"))
            do_jhove(fpath, dest)


    for i, f in enumerate([x for x in os.listdir(jhoves)]):

        f_path = os.path.join(jhoves, f)
        with open(f_path) as data:
            text = data.read()
            errors = {}
            if "Status: Well-Formed and valid" not in text:
                

                for line in text.split("\n"):

                    if "RepresentationInformation" in line:
                        line = line.replace("RepresentationInformation: ", "").strip()
                        my_ie = None
                        my_file_pid = None
                        parts = line.split(os.sep)
                        my_file_name = parts[-1] 

                        for p in parts:
                            if p.lower().startswith('fl'):
                                my_file_pid = p

                            if p.lower().startswith('ie'):
                                my_ie = p



                    if "message" in line.lower():
                        # print (line)
                        line = line.replace("ErrorMessage: ", "")
                        line = line.strip()

                        ### cleans ###
                        if "out of sequence" in line:
                            line = f"Out of sequence:{line}"
                        if line == "Validation ended prematurely due to an unhandled exception.":
                            line = "Validation ended prematurely due to an unhandled exception.:"

                        if line.startswith("Type mismatch"):
                            line ="Type mismatch:"+line
                        ###############


                        try:
                            error, data = line.split(":", 1)
                        except:
                            print()
                            print (line)
                            print ("include line in cleans so there is a ':' to split on")
                            quit()
                        data = data.strip()


                        if error not in errors:
                            errors[error] = []
                        errors[error].append(data)

                print (f)
                if my_file_pid:
                    print (my_file_pid)
                elif my_ie:
                    print (my_ie)


                for k, my_data in errors.items():
                    print ("\t", k, len(my_data)) 

                print ()

    return i+1


folder = r'C:\collections\xfmt-387\x_fmt_387_4_done'   
flush = True
count = do_summary(folder)

print ("Files in set:", count)