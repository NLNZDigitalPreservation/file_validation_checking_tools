import os
import subprocess
import shutil

def get_done(f):
    with open (f) as data:
        done = [x for x in data.read().split("\n") if x != '']
        print (f"Ignoring {len(done)} files - already processed")
        # for d in done:
        #     print (d)

        # quit()
        return done


def do_jhove(f, dest):
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
    cmd = f'''jhove {module} "{f}" > "{dest}"'''
    subprocess.call(cmd, shell=True)

def get_files_list(root):
    files = []
    for folder in os.listdir(root):
        if folder in done:
            pass
        if folder not in done:
            for f in os.listdir(os.path.join(root, folder)):
                files.append([os.path.join(root, folder, f), f])
    return files

def do_summary(folder):    
    # if not os.path.exists(jhoves):
    #     os.makedirs(jhoves)
    files = get_files_list(folder)
    # if flush:
    #     shutil.rmtree(jhoves)
    #     os.makedirs(jhoves)

    #     for f in files:
    #         fpath, fname = f
    #         fname, ext = fname.rsplit(".", 1)
    #         dest = os.path.join(jhoves, fname+".txt")
    #         do_jhove(fpath, dest)



    aggregator = {}
    solo_issues = {}   

    no_error = [] 

    for i, f in enumerate([x for x in os.listdir(jhoves) if x.replace(".txt", "") not in done]):
        f_path = os.path.join(jhoves, f)
        with open(f_path) as data:
            text = data.read()
            errors = {}
            if "Status: Well-Formed and valid" not in text:
                error_collector = {}

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
                        line = line.replace("ErrorMessage: ", "")
                        line = line.strip()

                        ### cleans ###
                        if "out of sequence" in line:
                            line = f"Out of sequence:{line}"

                        if line == "Validation ended prematurely due to an unhandled exception.":
                            line = "Validation ended prematurely due to an unhandled exception.:"

                        if line.startswith("Type mismatch"):
                            line ="Type mismatch:"+line

                        if line.startswith("Premature EOF"):
                            line = "Premature EOF:"

                        if line ==  "Bad ICCProfile in tag 34675; message Invalid ICC Profile Data":
                            line = "Bad ICCProfile:Bad ICCProfile in tag 34675"
                        
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

                        if error not in aggregator:
                            aggregator[error] = []

                        if f not in aggregator[error]:
                            aggregator[error].append(f)

                    

                print (my_file_pid)
                for k, my_data in errors.items():
                    print ("\t", k, len(my_data)) 
                print ()
                
                if len(errors) == 1:
                    for error in errors:
                        if error not in solo_issues:
                            solo_issues[error] = []
                        if my_file_pid:
                             solo_issues[error].append(my_file_pid)
                        elif my_ie:
                            solo_issues[error].append(my_ie)

    return i+1, aggregator, solo_issues, no_error

done_f = r"E:\tools\file_validation_checking_tools\done_pids\fmt_353.txt"
folder = r'\\wlgprdfile13\dfs_shares\ndha\dps_export_prod\gattusoj\export\ies\fmt_353'
jhoves = r"\\wlgprdfile12\home$\Wellington\GattusoJ\HomeData\Desktop\clean_up_part_2\jhove_reports\fmt_353"  
flush = False
done = get_done(done_f)
count, aggregator, solo_issues, no_error = do_summary(folder)


print ("\nFiles in set:", count, "\n")

print ("\nAll issues in corpus\n")
for k, v in aggregator.items():
    print (k, " - Count:", len(v))
    print ([x.replace(".txt", "") for x in v])
    print ()

print ()
print ("\nItems with only one issue\n")

for k, v in solo_issues.items():
    print (k, " - Count:", len(v))
    print (v)
    print ()

print ()
print (no_error)
