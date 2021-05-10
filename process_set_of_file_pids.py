import os
import subprocess
import shutil
from distutils.dir_util import copy_tree
import hashlib

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

#### reminder of issue #####
#  This is the product of the of the jhove analysis tool 'get_jhove_errors_from_set.py"
#  Using this tool generate potental cohorts and their PIDs  
#
# Premature EOF  - Count: 6
# ['FL28396694', 'FL36355934', 'FL25836881', 'FL8868088', 'FL20401467', 'FL12111455']
# 
# \\filestore\gattusoj\export\ies\fmt_353
# E:\fmt_353
# 
############################

### where the files are
root = r"E:\fmt_353"


### where the cohort needs to go (final folder is cohort id) 
temp_set_folder = r"E:\temp_fmt_353_3"


files_folder = os.path.join(temp_set_folder, "originals")

if not os.path.exists(temp_set_folder):
    os.makedirs(temp_set_folder)
if not os.path.exists(files_folder):
    os.makedirs(files_folder)

#####  starting place is a list of PID ids for a given cohort
pids = ['FL40326811', 'FL40326814', 'FL40326820', 'FL40326817', 'FL50181908', 'FL992978', 'FL819960', 'FL993061', 'FL993041', 'FL992867', 'FL993076', 'FL993047', 'FL819940', 'FL992975', 'FL819993', 'FL820205', 'FL820237', 'FL790126', 'FL819990', 'FL790071', 'FL820072', 'FL819996', 'FL991646', 'FL820202', 'FL820225', 'FL820222', 'FL820033', 'FL819999', 'FL790123', 'FL819899', 'FL819893', 'FL820014', 'FL820011', 'FL982860', 'FL820008', 'FL953588', 'FL820078', 'FL953597', 'FL992931', 'FL953602', 'FL992937', 'FL819975', 'FL991418', 'FL992925', 'FL2102776', 'FL2102822', 'FL2102828', 'FL2102887', 'FL2102889', 'FL2102834', 'FL2102832', 'FL2102898', 'FL2102896', 'FL2102900', 'FL2102892', 'FL2102905', 'FL2102903', 'FL2102880', 'FL2102836', 'FL2102895', 'FL983402', 'FL790108', 'FL819946', 'FL820021', 'FL819917', 'FL819987', 'FL820270', 'FL820217', 'FL979692', 'FL819896', 'FL790074', 'FL819911', 'FL953594', 'FL979674', 'FL820267', 'FL820264', 'FL953490', 'FL820039', 'FL991511', 'FL979644', 'FL820214', 'FL819934', 'FL819984', 'FL979629']


##### pick up all the pids in the cohot and copy them to the cohort folder
for pid in pids:
    for f in os.listdir(os.path.join(root, pid)):
        my_item_folder = os.path.join(files_folder, pid)
        my_file  = (os.path.join(root, pid, f))
        if not os.path.exists(my_item_folder):
            os.makedirs(my_item_folder)

        shutil.copy2(my_file, my_item_folder)


