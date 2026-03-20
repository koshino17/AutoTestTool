#!/usr/bin/env python3
#-*-coding:utf-8-*-

from tkinter import *
from tkinter import ttk
from tkinter import messagebox as mBox
from tkinter import scrolledtext
from tkinter.filedialog import askopenfilename

import sys, os
import subprocess
from datetime import datetime
from datetime import timedelta
import time

import re
import collections
import shutil
import threading
import platform
import csv
import json

tool_ver = 'v1.3' 

#=====================
#===Global Variable===
#=====================
is_Windows_OS = True if platform.system().lower()=='windows' else False
autotest_processing = False
autotest_abort = False
autotest_file_loaded = False
autotest_cmd_list = collections.OrderedDict()

m_gap_x=8
m_gap_y=4
c_gap_x=4
c_gap_y=2

parameter_sn = "sn_auto"

#=====================
#===Global function===
#=====================
def Create_Log_folder(foldername):
    try:
        #foldername = datetime.strftime(datetime.now(),"%Y%m%d_%H%M%S")
        os.makedirs(foldername)
    except FileExistsError:
        #gui_printmsg('err', f'\'{foldername}\' Folder already exist!\n')
        pass
    except PermissionError:
        gui_printmsg('err', f'PermissionError: Can not create \'{foldername}\' Folder...\n')

def Move_RD_Log(foldername, chip):
    #\RD_LOG\auto\20250221\auto
    if chLoopVar.get() == 1:
        return
    date = datetime.strftime(datetime.now(),"%Y%m%d")
    if chip == "":
        source_folder = os.path.join("RD_LOG", parameter_sn, date, parameter_sn)
    else:
        source_folder = os.path.join("RD_LOG", parameter_sn, date, chip)
    destination_folder = os.path.join(foldername, "RD_LOG")

    if os.path.isdir(source_folder):
        try:
            shutil.move(source_folder, destination_folder)
        except Exception as e:
            ErrortoWindow( f"  Move RD_LOG failed: {e}\n" )
    else:
        ErrortoWindow( f"  {source_folder} not found.\n" )

def parsing_autotest_csv(filename):
    global autotest_file_loaded, autotest_cmd_list
    autotest_file_loaded=False
    autotest_cmd_list.clear()

    index = 0
    try:
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for item in reader:
                if item.get('Status (Y/N)') == 'Y' and item.get("TestCase"):
                    index += 1
                    autotest_cmd_list[f"{index}"] = {
                        "Project": item["Project"].strip(),
                        "Chip": item.get("Chip", "").strip(),
                        "TestCase": item["TestCase"].strip(),
                        "ComPort": item["ComPort"].strip(),
                        "TestType": item["TestType"].strip(),
                        "Ext_Parameter": item["Ext_Parameter"].strip(),
                        "SpecFile": item.get("SpecFile", "").strip(),
                    }
        if len(autotest_cmd_list) > 0:
            autotest_file_loaded = True
            HighlighttoWindow( f"Load autotest File successfully\n" )
        else:
            ErrortoWindow( f"No enabled test cases found in {filename}\n" )
    except Exception as e:
        ErrortoWindow(f"CSV Parsing Error: {e}\n")

def updatetime_thread_func():
    start_time = datetime.now()
    while(autotest_processing):
        str_processtime = str(datetime.now()-start_time)[:10]
        sit_show_time.set( str_processtime )
        time.sleep(0.3)

def convert_to_seconds(time_str):
    try:
        (h, m, s) = time_str.split(':')
        delta = timedelta(hours=int(h), minutes=int(m), seconds=float(s))  
        return delta.total_seconds()
    except:
        return 0.0

def autotest_thread_func():
    global autotest_processing, autotest_abort

    file_import_button.config(state=DISABLED)
    start_button.config(state=DISABLED)
    finish_button.config(state=NORMAL)

    source_file = "output.log"
    timefolder = datetime.strftime(datetime.now(),"%Y%m%d_%H%M%S")
    foldername = os.path.join("AUTO_TEST_LOG", timefolder)
    Create_Log_folder(foldername)
    
    test_done = True
    loop_count = 0
    keep_running = True

    def is_in_range(val_str, crit_str):
        if "~" in crit_str:
            try:
                val = float(val_str)
                low, high = map(float, crit_str.split('~'))
                return low <= val <= high
            except: return False
        return crit_str.lower() in val_str.lower()

    while keep_running and not autotest_abort:
        loop_count += 1
        if loop_count > 1 and loop_count % 10 == 1:
            autotest_result_text.delete(1.0, END)
            HighlighttoWindow(f"--- Cleared log window for performance (Round {loop_count}) ---\n")
            
        HighlighttoWindow(f"\n--- Start Loop Round: {loop_count} ---\n")
        
        for idx in autotest_cmd_list:
            if autotest_abort:
                keep_running = False
                break
            
            time.sleep(1)
            prj = autotest_cmd_list[idx].get("Project")
            chip = autotest_cmd_list[idx].get("Chip")
            cmd = autotest_cmd_list[idx].get("TestCase")
            comport = autotest_cmd_list[idx].get("ComPort")
            test_type = autotest_cmd_list[idx].get("TestType")
            ext_par = autotest_cmd_list[idx].get("Ext_Parameter")
            spec_file = autotest_cmd_list[idx].get("SpecFile", "")

            if cmd.startswith("WAIT"):
                wait_time = float(cmd.split(":")[1])
                HighlighttoWindow(f"     --- wait {wait_time} second---\n")
                for _ in range(int(wait_time * 2)):
                    if autotest_abort: break
                    time.sleep(0.5)
                continue
            elif cmd.startswith("POPMSG"):
                pop_msg = cmd.split(':')[1].strip()
                HighlighttoWindow(f"     --- {pop_msg} ---\n")
                mBox.showwarning("Notice", pop_msg)
                continue

            if os.path.exists(source_file):
                for _ in range(5):
                    try:
                        os.remove(source_file)
                        break
                    except PermissionError:
                        time.sleep(0.5)

            MsgtoWindow( f'[{loop_count}] {idx}'.rjust(6) + "  " + cmd.ljust(30) )
            
            if prj == "": continue
            mtp_cmd = f"python mtp.py -s {parameter_sn} -p {prj} -t {cmd}"
            if chip != "": mtp_cmd += f" -chip {chip}"
            if comport != "": mtp_cmd += f" -u {comport}"
            if test_type != "": mtp_cmd += f" -type {test_type}"
            if ext_par != "": mtp_cmd += f" -a {ext_par}"

            try:
                msg = subprocess.check_output(mtp_cmd, shell=True, stderr=subprocess.STDOUT, text=True, timeout=500)

                match = re.search(r"Execution time:\s*([\d:.]+)", msg)
                if match:
                    execution_time = match.group(1)
                    print_time = convert_to_seconds(execution_time)
                    MsgtoWindow(f"{print_time:.02f}".rjust(10))
                else:
                    MsgtoWindow("--".rjust(10))

                tout_cnt = 0
                max_tout_cnt = 20 if test_type == "" else 100
                while not os.path.exists(source_file) and tout_cnt < max_tout_cnt:
                    if autotest_abort: break
                    time.sleep(1)
                    tout_cnt += 1
                
                if not autotest_abort and tout_cnt < max_tout_cnt:
                    time.sleep(0.5)
                    dest_file = os.path.join(foldername, f"R{loop_count}_{idx}_{cmd}_{source_file}")
                    shutil.copyfile(source_file, dest_file)

                    if chLoopVar.get() == 0:
                        dest_file = os.path.join(foldername, f"R{loop_count}_{idx}_{cmd}_{source_file}")
                        try:
                            shutil.copyfile(source_file, dest_file)
                        except Exception as e:
                            print(f"Backup log failed: {e}")

                    with open(source_file, "r") as f:
                        all_lines = [line.strip().rstrip('C') for line in f.readlines() if line.strip()]

                        log_data_map = {}
                        for l in all_lines:
                            if "$$" in l and not any(k in l for k in ["06ACK", "05OK", "07DONE", "07FAIL"]):
                                parts = l.split('$$')
                                if len(parts) >= 3:
                                    clean_name = re.sub(r'^[0-9A-F]{2}', '', parts[1].strip())
                                    log_data_map[clean_name] = parts[2].strip()

                        target_names = []
                        expected_crits = []
                        check_enabled = False

                        if spec_file and spec_file.lower().endswith(".json") and os.path.exists(spec_file):
                            try:
                                with open(spec_file, 'r', encoding='utf-8') as jf:
                                    specs = json.load(jf)
                                    case_spec = specs.get(cmd, {})
                                    if case_spec.get("check_required") == "Y":
                                        check_enabled = True
                                        for item in case_spec.get("items", []):
                                            target_names.append(item["name"])
                                            expected_crits.append(item["criteria"])
                            except Exception as e:
                                ErrortoWindow(f"  JSON Load Error: {e}\n")

                        if not check_enabled:
                            raw_val_name = autotest_cmd_list[idx].get("value_name", "")
                            raw_crit = autotest_cmd_list[idx].get("criteria", "")
                            if not raw_val_name.lower().endswith(".json"):
                                target_names = [v.strip() for v in raw_val_name.split('\n') if v.strip()]
                                expected_crits = [c.strip() for c in raw_crit.split('\n') if c.strip()]
                                if target_names: check_enabled = True

                        all_items_pass = True
                        if check_enabled:
                            for i, t_name in enumerate(target_names):
                                e_crit = expected_crits[i] if i < len(expected_crits) else ""
                                actual = log_data_map.get(t_name, "")
                                if not actual or not is_in_range(actual, e_crit):
                                    all_items_pass = False; break

                        if all_items_pass:
                            for k, v in log_data_map.items():
                                if "FAIL" in v.upper():
                                    all_items_pass = False
                                    break

                        if all_items_pass:
                            ValuetoWindow("  PASS\n")
                        else:
                            ErrortoWindow("  FAIL\n")

                        displayed_keys = set()
                        for i, t_name in enumerate(target_names):
                            e_crit = expected_crits[i] if i < len(expected_crits) else ""
                            actual = log_data_map.get(t_name, "NOT FOUND")
                            displayed_keys.add(t_name)
                            
                            is_fail = (actual == "NOT FOUND") or (e_crit and not is_in_range(actual, e_crit))
                            MsgtoWindow(" " * 8 + f"- {t_name}".ljust(45))
                            if is_fail:
                                ErrortoWindow(f"({actual}) [Expect: {e_crit}]\n")
                            else:
                                ValuetoWindow(f"({actual})\n")

                        for k, v in log_data_map.items():
                            if k not in displayed_keys:
                                MsgtoWindow(" " * 8 + f"- {k}".ljust(45))
                                if "FAIL" in v.upper(): ErrortoWindow(f"({v})\n")
                                else: ValuetoWindow(f"({v})\n")

                        if not all_items_pass and chVar.get() == 1:
                            test_done = False; keep_running = False; break
                elif not autotest_abort:
                    ErrortoWindow(f"  timeout: no output.log\n")
                    if chVar.get() == 1: test_done = False; keep_running = False; break
            
            except Exception as e:
                if not autotest_abort:
                    ErrortoWindow(f"  Exec Error: {str(e)}\n")
                if chVar.get() == 1: test_done = False; keep_running = False; break

        if chLoopVar.get() == 0:
            keep_running = False

    if test_done and not autotest_abort:
        HighlighttoWindow(f'\n\n=== Auto Run Finished ({loop_count} Rounds) ===\n')
    else:
        ErrortoWindow(f'\n\n=== Auto Run Aborted ===\n')

    Move_RD_Log(foldername, chip)

    autotest_processing = False
    file_import_button.config(state=NORMAL)
    start_button.config(state=NORMAL)
    finish_button.config(text='ABORT', fg='red', state=DISABLED)

#========================
#===GUI echo functions===
#========================
def echo_load_file():
    fname = askopenfilename(filetypes=(("autotest file", "*.csv"),("All files", "*.*")))
    if fname:
        var_file_path.set(fname)
        parsing_autotest_csv(fname)

def echo_autotest_start():
    global autotest_processing, autotest_abort, parameter_sn
    if not autotest_file_loaded:
        mBox.showwarning("Notice", "Please import autotest file first...")
        return

    parameter_sn = var_sn.get().strip()
    if not parameter_sn:
        parameter_sn = "sn_auto"
    
    autotest_result_text.delete(1.0, END)
    autotest_abort = False
    autotest_processing = True
    
    threading.Thread(target=autotest_thread_func, daemon=True).start()
    threading.Thread(target=updatetime_thread_func, daemon=True).start()

def echo_autotest_end():
    global autotest_abort
    autotest_abort = True
    finish_button.config(text='Wait for Abort', fg='red', state=DISABLED)

def MsgtoWindow(str_msg):
    autotest_result_text.insert(END, str_msg, "info" )
    autotest_result_text.see(END)

def ErrortoWindow(str_msg):
    autotest_result_text.insert(END, str_msg, "error" )
    autotest_result_text.see(END)

def HighlighttoWindow(str_msg):
    autotest_result_text.insert(END, str_msg, "highlight" )
    autotest_result_text.see(END)

def ValuetoWindow(str_msg):
    autotest_result_text.insert(END, str_msg, "value" )
    autotest_result_text.see(END)

if __name__ == '__main__':
    frmMain = Tk()
    frmMain.title(f'MTP Auto Run Tool({tool_ver})')
    frmMain.resizable(0,0)

    file_group = LabelFrame(frmMain, text='Load Auto Test file', font=('Times New Roman', 10, 'bold'))
    file_group.grid(column=0, row=0, padx=m_gap_x, pady=m_gap_y, sticky='WE')
    Label(file_group, text='Serial Number: ').grid(column=0, row=0, padx=c_gap_x, pady=c_gap_y, sticky='W')
    var_sn = StringVar(value=parameter_sn)
    Entry(file_group, textvariable=var_sn, width=30).grid(column=1, row=0, padx=c_gap_x, pady=c_gap_y, sticky='W', columnspan=2)
    Label(file_group, text='Import file ').grid(column=0, row=1, padx=c_gap_x, pady=c_gap_y, sticky='W')
    var_file_path = StringVar()
    Entry(file_group, textvariable=var_file_path, width=50, state=DISABLED).grid(column=1, row=1, padx=c_gap_x, pady=c_gap_y, sticky='W')
    file_import_button = Button(file_group, text='Open CSV', fg='black', command=echo_load_file)
    file_import_button.grid(column=2, row=1, padx=c_gap_x, pady=c_gap_y, sticky='W')

    sit_group = LabelFrame(frmMain, text='Execution Control', font=('Times New Roman', 10, 'bold'))
    sit_group.grid(column=0, row=3, padx=m_gap_x, pady=m_gap_y, sticky='WE')
    Label(sit_group, text='Elapsed Time: ').grid(column=0, row=0, padx=c_gap_x, pady=c_gap_y, sticky='W')
    sit_show_time = StringVar()
    Entry(sit_group, textvariable=sit_show_time, width=20, state=DISABLED).grid(column=1, row=0, padx=c_gap_x, pady=c_gap_y, sticky='W')
    
    chVar = IntVar()
    Checkbutton(sit_group, text="Abort if fail", variable=chVar).grid(column=2, row=0, padx=c_gap_x, pady=c_gap_y, sticky='W')
    
    chLoopVar = IntVar()
    Checkbutton(sit_group, text="Loop Mode (Overnight)", variable=chLoopVar).grid(column=3, row=0, padx=c_gap_x, pady=c_gap_y, sticky='W')
    
    start_button = Button(sit_group, text='START', fg='blue', command=echo_autotest_start)
    start_button.grid(column=4, row=0, padx=c_gap_x*2, pady=c_gap_y, sticky='E')
    finish_button = Button(sit_group, text='ABORT', fg='red', command=echo_autotest_end, state=DISABLED)
    finish_button.grid(column=5, row=0, padx=c_gap_x*2, pady=c_gap_y, sticky='E')

    autotest_result_text = scrolledtext.ScrolledText(sit_group, width=100, height=60, wrap=WORD)
    autotest_result_text.tag_config('info', foreground='black')
    autotest_result_text.tag_config('error', foreground='red')
    autotest_result_text.tag_config('highlight', foreground='blue')
    autotest_result_text.tag_config('value', foreground='green')
    autotest_result_text.grid(column=0, row=1, padx=c_gap_x, pady=c_gap_y*2, sticky='WE', columnspan=6)
    
    frmMain.mainloop()