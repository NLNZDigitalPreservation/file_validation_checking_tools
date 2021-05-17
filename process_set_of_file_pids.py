import os
import subprocess
import shutil
from distutils.dir_util import copy_tree
import hashlib
import pickle
script_root = r"\\wlgprdfile12\home$\Wellington\GattusoJ\homedata\Desktop\clean_up_part_2"


def get_done(f):
    with open (f) as data:
        done = [x for x in data.read().split("\n") if x != '']
        return done

def clean_up_done():
    with open (done_f, "w") as data:
        data.write("\n".join(set(done)))

def get_lookup():
    rosetta_csv = os.path.join(script_root, "rosetta_data.csv")
    files_pickle = os.path.join(script_root, "rosetta_data.pickle")
    if os.path.exists(files_pickle):
        return pickle.load( open( files_pickle, "rb" ) )
    else:
        files = {}
        with open(rosetta_csv, encoding="utf8") as data:
            reader = csv.reader(data)
            for r in reader:
                ie, rep_pid, file_pid, file_name, pres_type, is_valid, is_well_formed, alma, tiaka, size_bytes, ext, puid = r
                files[file_pid] = (ie, rep_pid, file_pid, file_name, pres_type, is_valid, is_well_formed, alma, tiaka, size_bytes, ext, puid)
        pickle.dump( files, open( files_pickle, "wb" ) )
        return files
look_up = get_lookup()

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def make_subset(done):
    files_folder_fixed = os.path.join(temp_set_folder, "fixed")
    files_folder_original = os.path.join(temp_set_folder, "original")

    if not os.path.exists(temp_set_folder):
        os.makedirs(temp_set_folder)

    if not os.path.exists(files_folder_fixed):
        os.makedirs(files_folder_fixed)

    if not os.path.exists(files_folder_original):
        os.makedirs(files_folder_original)



    for pid in pids:
        for f in os.listdir(os.path.join(root, pid)):
            my_fixed_item_folder = os.path.join(files_folder_fixed, pid)
            my_original_item_folder = os.path.join(files_folder_original, pid)
            
            my_file  = (os.path.join(root, pid, f))
            done.append(pid)

            

            if not os.path.exists(my_original_item_folder):
                os.makedirs(my_original_item_folder)        
            if not os.path.exists(my_fixed_item_folder):
                os.makedirs(my_fixed_item_folder)

            shutil.copy2(my_file, my_fixed_item_folder)
            shutil.copy2(my_file, my_original_item_folder)


    for folder in [files_folder_fixed, files_folder_original]:

        for pid in os.listdir(folder):
            og_filename = look_up[pid][3]
            my_pid = os.path.join(folder, pid)

            for f in [x for x in os.listdir(my_pid)]:
                if f.endswith("_original"):
                    os.remove(os.path.join(folder, my_pid, f))

                elif f != og_filename:
                    in_name = os.path.join(my_pid, f)
                    out_name = os.path.join(my_pid, og_filename)
                    print (f"fixing: {f}")
                    os.rename(in_name, out_name)

    print (f"Copied {len(pids)} file(s)")
    print (f"Destination: {temp_set_folder}")
    return done

##############################

pids = ['FL597049', 'FL599910', 'FL601051', 'FL602228', 'FL972959', 'FL972962']

pids = [x.replace(".txt", "") for x in pids]
done_f = r"E:\tools\file_validation_checking_tools\done_pids\fmt_353.txt"
root = r"E:\fmt_353"
temp_set_folder = r"E:\fmt_353_13"


done = get_done(done_f)
done = make_subset(done)
clean_up_done()

print ()
