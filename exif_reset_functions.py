import os
import subprocess

"""requires exiftool to be visible to commandline"""


def reset_exif(infile, outfile):
    cmd = f'exiftool.exe -TagsFromFile "{infile}" "{outfile}"'
    subprocess.call(cmd, shell=True)

def make_sub_folders_copy_file_reset_exif(infile, outroot):
    if not os.path.exists(outroot):
        os.makedirs(outroot)
    shutil.copy2(infile, outroot)
    cmd = f'exiftool.exe -TagsFromFile "{infile}" "{outfile}"'
    subprocess.call(cmd, shell=True)


def original_exif_to_existing_copy_of_a_file_by_folder(in_root, out_root):
    """ expects a 2nd folder that contains the files
        <root>
            <pid>
                file(s)

    must be mirrored in out-folder. 

    remove first loop if files are directly in root folder"""

    for pid in os.listdir(in_root):
        in_pid = os.path.join(in_root,pid)
        for f in os.listdir(in_pid):
            infile = os.path.join(in_pid, f)
            outfile = infile.replace(in_root, out_root)
            print (os.path.exists(infile), os.path.exists(infile), infile, outfile)
            reset_exif(infile, outfile)
            print ()


def  original_exif_to_new_copy_of_a_file_by_folder(in_root, out_root):
    """ expects a 2nd folder that contains the files
        <root>
            <pid>
                file(s)

    will be mirrored in out-folder. 

    remove first loop if files are directly in root folder"""

    for pid in os.listdir(in_root):
        in_pid = os.path.join(in_root,pid)
        for f in os.listdir(in_pid):
            infile = os.path.join(in_pid, f)
            outfile = infile.replace(in_root, out_root)
            my_out_root = os.path.join(out_root, pid)
            if not os.path.exists(my_out_root):
                os.makedirs(my_out_root)
            shutil.copy2(infile, outfile)
            print (os.path.exists(infile), os.path.exists(infile), infile, outfile)
            reset_exif(infile, outfile)
            print ()



##### Example usage

# #### add original exif to existing copy of a file by folder:
# in_root = r"c:\original_files"
# out_root = r"c:\copies_to_be_fixed"
# original_exif_to_existing_copy_of_a_file_by_folder(in_root, out_root) 


# #### add original exif to new copy of a file by folder:
# in_root = r"c:\original_files"
# out_root =r"c:\new_folder_for_fixed_files"
# original_exif_to_new_copy_of_a_file_by_folder(in_root, out_root)

# ####### single file without existing copy
# infile = r"c:\original_files\my_tif.tif"
# outfile =r"c:\new_folder_for_fixed_files\my_tif.tif"
# reset_exif(infile, outfile)


# make_sub_folders_copy_file_reset_exif(infile, outroot)
# infile = r"c:\original_files\my_tif.tif"
# outroot = r"c:\copies_to_be_fixed"
# make_sub_folders_copy_file_reset_exif(infile, outroot)
