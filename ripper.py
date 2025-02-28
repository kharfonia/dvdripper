from __future__ import annotations
from typing import List
import pyudev
import subprocess
import re
import sys
import os
import datetime
import time
from logger import Logger, LogLevel, ConsoleLogHandler, FileLogHandler

import threading
import shutil

logger_file = "log.txt"
dvd_dump_dir = "./dvd_dump"
mkv_dump_dir = "./mkv_dump"
min_length_sec = 240

logger = Logger()
logger.add_handler(ConsoleLogHandler(LogLevel.INFO))
logger.add_handler(FileLogHandler(logger_file, LogLevel.DEBUG))


def find_file(root_dir, filename):
    for dirpath, _, files in os.walk(root_dir):
        if filename in files:
            return os.path.join(dirpath, filename)
    return None

def eject_dvd(device:str):
    try:
        subprocess.run(["eject", device], check=True)
        print(f"DVD ejected from {device}")
    except subprocess.CalledProcessError as e:
        print(f"Error ejecting DVD: {e}")


class RipCollection:
    def __init__(self):
        self.items: List[RipItem] = []
        self.counter = 0

    def add(self, item: RipItem):
        self.counter += 1
        item.id = self.counter
        self.items.append(item)

    def get_by_id(self, id:int)->RipItem:
        for rip in self.items:
            if rip.id == id: return rip
        return None

    def remove(self, items: RipItem|list[RipItem]):
        if isinstance(items, RipItem):
            items = [items]
        for item in items:
            self.items.remove(item)
            shutil.rmtree(item.dvd_dump_path)
            shutil.rmtree(item.mkv_dump_path)
    
    def scan(self, path: str):
        for filename in os.listdir(path):
            if os.path.isdir(path + "/" + filename):
                x = RipItem("", dvd_dump_dir, mkv_dump_dir, filename)
                x.status = "Loaded from disk"
                x.findDumpedItems()
                self.add(x)

    def to_dict(self):
        return {
            'items': [item.to_dict() for item in self.items],
            'counter': self.counter
        }

    

class FileItem:
    def __init__(self, filename: str, path: str):
        self.filename = filename
        self.path = path
        self.size = os.path.getsize(path)
        self.rename_to = None

    def to_dict(self):
        return {

            'filename': self.filename,
            'path': self.path,
            'size': self.size,
            'rename_to': self.rename_to
        }


Rip_Collection = RipCollection()

class RipItem:
    def __init__(self, device: str, dvd_dump_path: str, mkv_dump_path: str, title: str = None):
        self.device = device
        self.title = title or self.get_dvd_title()
        self.dvd_dump_path = dvd_dump_path + "/" + self.title
        self.mkv_dump_path = mkv_dump_path + "/" + self.title
        self.dt = datetime.datetime.now().isoformat()
        self.rip_from_dvd_done = False
        self.rip_to_mkv_done = False
        self.dvd_dump_path2: str = None
        self.mkv_dump_files: List[FileItem] = []
        self.mass_rename_mkv_prefix = None
        self.status = "Initialising"
        self.id = -1

    def set_title(self, title: str):
        self.title = title
        os.rename(self.dvd_dump_path, dvd_dump_dir + "/" + title)
        os.rename(self.mkv_dump_path, mkv_dump_dir + "/" + title)
        self.dvd_dump_path = dvd_dump_dir + "/" + title
        self.mkv_dump_path = mkv_dump_dir + "/" + title
        for file in self.mkv_dump_files:
            file.path = os.path.join(self.mkv_dump_path, file.filename)

    def get_dvd_title(self):
        self.status = "Getting DVD title"
        # Use lsdvd to get the DVD title
        result = subprocess.run(['lsdvd', self.device], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        for line in output.split('\n'):
            if line.startswith('Disc Title:'):
                self.status = "Getting DVD title [DONE]"
                return line.split(':')[1].strip()
        self.status = "Getting DVD title [None found]"
        return None

    def rip_dvd_to_folder(self):
        self.status = "Ripping DVD to folder"
        if os.path.exists(self.dvd_dump_path):
            self.dvd_dump_path = self.dvd_dump_path + "_" + self.dt
        os.makedirs(self.dvd_dump_path)
        logger.log(f"Ripping DVD ({self.device}) to folder ({self.dvd_dump_path}).", LogLevel.INFO)
        exec = ['dvdbackup', '-i', self.device, '-M', '-p', '-o', self.dvd_dump_path]
        logger.log(" ".join(exec), LogLevel.INFO)
        process = subprocess.Popen(exec, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        for line in iter(process.stdout.readline, ''):
            if len(line) == 0:
                break
            logger.log(line.decode('utf-8'), LogLevel.INFO)

        process.stdout.close()
        process.wait()
        self.status = "Ripping DVD to folder [DONE]"

    def rip_folder_to_mkv(self):
        self.status = "Ripping folder to mkv"
        if os.path.exists(self.mkv_dump_path):
            self.mkv_dump_path = self.mkv_dump_path + "_" + self.dt
        os.makedirs(self.mkv_dump_path)
        logger.log(f"Ripping folder ({self.dvd_dump_path}) to mkv ({self.mkv_dump_path}).", LogLevel.INFO)

        folder_path = find_file(self.dvd_dump_path, "VIDEO_TS.IFO")
        exec = ['makemkvcon', '--noscan', '--minlength=0', 'mkv', 'file:' + folder_path, 'all', self.mkv_dump_path]
        logger.log(" ".join(exec), LogLevel.INFO)
        process = subprocess.Popen(exec, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        for line in iter(process.stdout.readline, ''):
            if len(line) == 0:
                break
            sys.stdout.write(line.decode('utf-8'))
            sys.stdout.flush()
        process.stdout.close()
        process.wait()
        self.status = "Ripping folder to mkv [DONE]"

    def findDumpedItems(self):
        # find all files in the mkv_dump_path folder
        self.mkv_dump_files.clear()
        files = os.listdir(self.mkv_dump_path)
        files.sort()
        for filename in files:
            if filename.endswith(".mkv"):
                file_path = os.path.join(self.mkv_dump_path, filename)
                self.mkv_dump_files.append(FileItem(filename, file_path))
        ld = os.listdir(self.dvd_dump_path)
        if len(ld) >= 1:
            self.dvd_dump_path2 = self.dvd_dump_path + "/" + ld[0]

    def mass_rename_mkv(self, new_name: str):
        self.mass_rename_mkv_prefix = new_name
        for file in self.mkv_dump_files:
            file.rename_to = new_name + '_' + file.filename

    def do_rename(self):
        for file in self.mkv_dump_files:
            if file.rename_to is not None:
                os.rename(file.path, os.path.join(self.mkv_dump_path, file.rename_to))
                file.filename = file.rename_to
                file.path = os.path.join(self.mkv_dump_path, file.rename_to)
                file.rename_to = None

    def get_mkv_file(self, filename: str)->FileItem:
        for f in self.mkv_dump_files:
            if f.filename == filename: return f
        return None

    def delete_mkv_file(self, filename: str):
#        print("ripper.delete_mkv file Deleting: ", filename)
#        print("ripper.delete_mkv file Files: ", ", ".join(i.filename for i in self.mkv_dump_files))
        files = [file for file in self.mkv_dump_files if file.filename == filename]
        for file in files:
            self.mkv_dump_files.remove(file)
            os.remove(os.path.join(self.mkv_dump_path, file.filename))

#        self.mkv_dump_files = [file for file in self.mkv_dump_files if file.filename != filename]
#        os.remove(os.path.join(self.mkv_dump_path, filename))

    def __str__(self):
        mkv_files_str = "\n".join([f'\t\t{file.filename} ({file.size / (1024 * 1024):.2f} MB)' for file in self.mkv_dump_files])
        return f"""
RipItem: {self.title} ({self.device})
\tDVD dump path: {self.dvd_dump_path}
\tMKV dump path: {self.mkv_dump_path}
\tDVD dump path2: {self.dvd_dump_path2}
\tMKV files:
{mkv_files_str}
"""
    
    def to_dict(self):
        return {
            'device': self.device,
            'title': self.title,
            'dvd_dump_path': self.dvd_dump_path,
            'mkv_dump_path': self.mkv_dump_path,
            'dt': self.dt,
            'rip_from_dvd_done': self.rip_from_dvd_done,
            'rip_to_mkv_done': self.rip_to_mkv_done,
            'dvd_dump_path2': self.dvd_dump_path2,
            'mkv_dump_files': [file.to_dict() for file in self.mkv_dump_files],
            'mass_rename_mkv_prefix': self.mass_rename_mkv_prefix,
            'status': self.status,
            'id': self.id
        }
        

        
        
        
def dvd_inserted(device: str):
    logger.log("dvd inserted: " + device, LogLevel.INFO)
    try:
        rip_item = RipItem(device, dvd_dump_dir, mkv_dump_dir)
        Rip_Collection.add(rip_item)

        logger.log("dvd title: " + rip_item.title, LogLevel.INFO)
        rip_item.rip_dvd_to_folder()
        rip_item.rip_folder_to_mkv()
        rip_item.findDumpedItems()
        logger.log(str(rip_item),LogLevel.DEBUG)
    except Exception as e:
        logger.log(f"Error while ripping {device}: {e}")
    try:    
        eject_dvd(device)
    except Exception as e:
        if device not in devices_in_use.keys: return
        devices_in_use.pop(device)
        dvd_removed(device)



def dvd_removed(device: str):
    logger.log("dvd removed: " + device, LogLevel.INFO)

class DeviceThreadMap:
    def __init__(self, device:str):
        self.device = device
        self.thread:threading.Thread = None

devices_in_use:dict[str, DeviceThreadMap]={}

def dvd_listener():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="block")
    logger.log("Waiting for DVD insert/remove events...", LogLevel.INFO)

    for device in iter(monitor.poll, None):
        #logger.log(f"Device action: {device.action}");
        if device.properties.get('ID_CDROM_MEDIA_DVD', "0") == "1":
            d=DeviceThreadMap(device.device_node)
            if d.device in devices_in_use.keys(): continue
            devices_in_use[d.device] = d
            logger.log(f"Device {device.device_node} inserted.", LogLevel.INFO)

            d.thread = threading.Thread(target=dvd_inserted, args=[d.device], daemon=True)
            d.thread.start()
        else:
            if device.device_node not in devices_in_use.keys(): continue
            devices_in_use.pop(device.device_node)
            dvd_removed(device.device_node)
        print (devices_in_use)


def dvd_listener_backgroud():
    listener_thread = threading.Thread(target=dvd_listener, daemon=True)
    listener_thread.start()
    logger.log("DVD listener started in the background.", LogLevel.INFO)

def main():
    dvd_listener_backgroud()
    while (True):
        time.sleep(1)  # Sleep for 1 second to reduce CPU usage
        if input() == 'q':
            break




if __name__ == '__main__':
    # main()
    # dvd_inserted("/dev/sr0")

    Rip_Collection.scan(dvd_dump_dir)
    for rip_item in Rip_Collection.items:
        print(rip_item)
    main()
