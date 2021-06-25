"""
Connect to an input SSID on an input BSSID
"""
import traceback
import json
import shutil
import time
import syslog
import argparse
import netifaces as ni
import subprocess as sp
import os.path

import ansible.constants as C
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import bssid_validator


DEBUG = False


class ResultCallback(CallbackBase):
    """
    A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def v2_runner_on_ok(self, result, **kwargs):
        """
        Print a json representation of the result
        """
        host = result._host
        if DEBUG:
            print(json.dumps({host.name: result._result}, indent=4))


def set_flags(auth):
    """
    Extract connection flags from auth object
    """
    paranoid = pscheduler_restart = apache_restart = postgres_restart = False
    wait_time = 0

    # Defaults can be changed by input object
    if 'paranoid' in auth['connection_flags']:
        paranoid = auth['connection_flags']['paranoid']

    if 'pscheduler_restart' in auth['connection_flags']:
        pscheduler_restart = auth['connection_flags']['pscheduler_restart']

    if 'apache_restart' in auth['connection_flags']:
        apache_restart = auth['connection_flags']['apache_restart']

    if 'postgres_restart' in auth['connection_flags']:
        postgres_restart = auth['connection_flags']['postgres_restart']

    if 'wait_time' in auth['connection_flags']:
        wait_time = auth['connection_flags']['wait_time']

    flags = {
        "paranoid": paranoid,
        "pscheduler_restart": pscheduler_restart,
        "apache_restart": apache_restart,
        "postgres_restart": postgres_restart,
        "wait_time": wait_time
    }

    return flags


def test_connection(ssid, bssid, interface):
    """
    Start connection attempt after command line call
    Take in arguments on the command line
    """
    AuthMethod = { "type": "user", "identity": "fakeUID", "password": "fakePassword",\
        "connection_flags": {
            "paranoid": False,
            "pscheduler_restart": False,
            "apache_restart": False,
            "postgres_restart": False,
            "wait_time": 0 }
        }
    prepare_connection(ssid, bssid, interface, AuthMethod)


def subprocess_calls(args, check=True):
    sp_output = sp.run(args, shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    if check: assert(sp_output.returncode == 0)
        

def return_and_log(connected, json_info):
    # Log status of connection
    if connected:
        log_msg = 'Connected: ' + json_info
        syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, log_msg)
    else:
        log_msg = 'Failed to connect: ' + json_info
        syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, log_msg)

    return json_info


def prepare_connection(ssid, bssid, interface, auth):
    """
    Prepare a connection to a given ssid and bssid using wpa_supplicant
    Configure and connect on given interface
    Decide connect method and config file based on auth
    """
    connect_msg = "Connecting to " + ssid + " on " + bssid
    syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, connect_msg)

    connected = False
    connection_info = {}
    connection_info['ssid'] = ssid
    connection_info['bssid'] = bssid
    connection_info['time'] = None
    connection_info['new_ip'] = None
    connection_info['operation'] = 'connection'
    connection_info['connected'] = connected

    json_info = json.dumps(connection_info)

    # Start timing connection
    start_time = time.time()

    wpa_supp_path = '/etc/wpa_supplicant/wpa_supplicant_' + ssid + '.conf'

    # Format SSID and BSSID for wpa supplicant
    ssid_line = '    ssid="' + ssid + '"\n'
    bssid_line = '    bssid=' + bssid + '\n'

    # Add interface to ip commands
    bring_down = ('ip link set ' + interface + ' down')
    flush_config = ('ip addr flush dev ' + interface)
    bring_up = ('ip link set ' + interface + ' up')

    # Add interface to wpa supplicant and dhclient commands
    run_wpa_supplicant = ('wpa_supplicant -B -c ' + wpa_supp_path + \
        ' -i ' + interface)
    dhclient = ('dhclient ' + interface)
    kill_dhclient = 'killall dhclient'
    dhclient_release = ('dhclient -r ' + interface)

    # import pdb; pdb.set_trace()
    if not os.path.exists(wpa_supp_path):
        return return_and_log(connected, json_info)
    
    try:
        subprocess_calls(dhclient_release, True)
        subprocess_calls(kill_dhclient, False)
        subprocess_calls('ip route del default', False)

        interface_path = '/var/run/wpa_supplicant/wlan0'
        if os.path.exists(interface_path):
            subprocess_calls('rm ' + interface_path, False)

        subprocess_calls('killall wpa_supplicant', False)
        subprocess_calls(bring_down)
        subprocess_calls(flush_config)
        subprocess_calls(bring_up)

        wpa_file = open(wpa_supp_path, "r")
        wpa_lines = wpa_file.readlines()
        wpa_file.close()
        wpa_file = open(wpa_supp_path, "w")
        for line in wpa_lines:
            if line.startswith('    ssid'):
                wpa_file.write(ssid_line)
            elif line.startswith('    bssid'):
                wpa_file.write(bssid_line)
            else: wpa_file.write(line)
        wpa_file.close()

        # import pdb; pdb.set_trace()
        subprocess_calls(run_wpa_supplicant)
        subprocess_calls(dhclient)
    except:
        return return_and_log(connected, json_info)


    # Run the playbook
    connected = True
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Check if connection is successful
    connected = bssid_validator.validate_connect(bssid)

    # Get ip
    ip_addr = 'Failed'
    try:
        ni.ifaddresses('wlan0')
        ip_addr = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
    except:
        connected = False
    
    connection_info = {}
    connection_info['ssid'] = ssid
    connection_info['bssid'] = bssid
    connection_info['time'] = elapsed_time
    connection_info['new_ip'] = ip_addr
    connection_info['operation'] = 'connection'
    connection_info['connected'] = connected

    json_info = json.dumps(connection_info)
    return return_and_log(connected, json_info)
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Connect')
    parser.add_argument('ssid', help='Enter ssid to connect to')
    parser.add_argument('bssid', \
            help='Enter bssid in format 00:11:22:33:44:55:66')
    parser.add_argument('interface', \
            help='Enter interface of wireless. Ex wlan0')
    args = parser.parse_args()
    test_connection(args.ssid, args.bssid, args.interface)
    exit(0)

