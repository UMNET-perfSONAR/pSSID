import pscheduler.batchprocessor

"""
Implement ssid scanner with the wifi library
Uses iwlist and must be run as root
"""

import json
import syslog
import argparse
import time
import netifaces as ni


def get_all_bssids(batch):
    """
    Scan the given interface for all bssids
    Return a list of json objects representing all bssids
    """
    start_time = time.time()
    processor = pscheduler.batchprocessor.BatchProcessor(batch)
    result = processor()
    cells = result["jobs"][0]["results"][0]["runs"][0]["application/json"]["ssid_list"]

    print(cells)
    wifi_list = []
    for cell in cells:
        bssid = json.dumps(cell)
        wifi_list.append(bssid)

    end_time = time.time()
    elapsed_time = end_time - start_time
    log_msg = "Scan finished in " + str(elapsed_time)

    syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, log_msg)

    return wifi_list, elapsed_time


def print_ssid(interface, ssid):
    """
    Scan on the given interface
    Return a list of all bssids with the given ssid
    """
    all_bssids, elapsed_time = get_all_bssids(interface)
    ssid_list = []

    # Check complete list for matching ssids
    for bssid in all_bssids:
        bssid = json.loads(bssid)
        if bssid['ssid'] == ssid:
            ssid_list.append(bssid)

    for entry in ssid_list:
        print(entry)


def is_rogue(bssid, ssid_list):
    rogue_ssid = True
    ssid = None

    for i in ssid_list:
        # for scan check if matches any other ssid
        if bssid["ssid"] == i["SSID"]:
            rogue_ssid = False
            ssid = i
            break

    return rogue_ssid, ssid


def channel_match(bssid, ssid):
    try:
        if bssid["channel"] not in ssid["channels"]:
            return False
    except:
        print("ERROR in channel_mismatch ", bssid, ssid)
        return False
    return True


def scan_qualify(bssid_list, ssid_list, unknown_SSID_warning):
    qualified_per_ssid = {}
    return_obj = []

    for i in ssid_list:
        qualified_per_ssid[i["SSID"]] = 0

    for bssid in bssid_list:
        try:
            bssid = json.loads(bssid)
        except:
            print(time.ctime(time.time()))
            print("ERROR in loading BSSID from bssid_list:", bssid_list)
            return

        checked_bssid = {}
        checked_bssid["BSSID"] = bssid
        checked_bssid["rogue_ssid"] = False
        checked_bssid["unknown_ssid_warning"] = unknown_SSID_warning
        checked_bssid["channel_mismatch"] = False
        checked_bssid["channel_mismatch_warning"] = False
        checked_bssid["good_signal"] = False

        rogue, ret_ssid = is_rogue(bssid, ssid_list)

        if rogue:
            checked_bssid["rogue_ssid"] = True
        elif not channel_match(bssid, ret_ssid):
            checked_bssid["channel_mismatch"] = True
            checked_bssid["channel_mismatch_warning"] = ret_ssid["channel_mismatch_warning"]
        elif bssid["signal"] >= ret_ssid["min_signal"]:
            checked_bssid["good_signal"] = True
            qualified_per_ssid[ret_ssid["SSID"]] += 1

        return_obj.append(checked_bssid)


    for j in ssid_list:
        if qualified_per_ssid[j["SSID"]] < j["min_qualifying"]:
            print("Too few qualified_bssids for", j["SSID"])


    return return_obj


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Scan')
    parser.add_argument('interface', help='Enter interface to scan on')
    parser.add_argument('ssid', help='Enter ssid to filter out')
    args = parser.parse_args()
    print_ssid(args.interface, args.ssid)
    exit(0)

