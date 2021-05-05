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
    AuthMethod = { "type": "User", "UID": "fakeUID", "Password": "fakePassword",\
            "connection_flags": {
                        "paranoid": False,
                        "pscheduler_restart": False,
                        "apache_restart": False,
                        "postgres_restart": False,
                        "wait_time": 0 }
            }
    prepare_connection(ssid, bssid, interface, AuthMethod)


def prepare_connection(ssid, bssid, interface, auth):
    """
    Prepare a connection to a given ssid and bssid using wpa_supplicant
    Configure and connect on given interface
    Decide connect method and config file based on auth
    """
    connect_msg = "Connecting to " + ssid + " on " + bssid
    syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, connect_msg)

    flags = set_flags(auth)

    # Start timing connection
    start_time = time.time()

    # Determine auth method
    if auth['type'] == 'MacAddress':
        print('Connect to MSetup')
        exit()

    elif auth['type'] == 'User':
        wpa_supp_path = '/etc/wpa_supplicant/wpa_supplicant_' + ssid + '.conf'
        if DEBUG:
            print('User auth')

    # Format SSID and BSSID for wpa supplicant
    ssid_line = '    ssid="' + ssid + '"'
    bssid_line = '    bssid=' + bssid

    # Add interface to ip commands
    bring_down = ('ip link set ' + interface + ' down')
    flush_config = ('ip addr flush dev ' + interface)
    bring_up = ('ip link set ' + interface + ' up')

    # Add interface to wpa supplicant and dhclient commands
    run_wpa_supplicant = ('wpa_supplicant -B -c ' + wpa_supp_path + \
            ' -i ' + interface)
    dhclient = ('dhclient ' + interface)
    dhclient_release = ('dhclient -r ' + interface)

    # since the API is constructed for CLI it expects certain options
    # to always be set in the context object
    context.CLIARGS = ImmutableDict(connection='local', \
            module_path=['/to/mymodules'], forks=10, become='yes', \
            become_method='su', become_user=None, check=False, diff=False)

    # initialize needed objects
    loader = DataLoader()
    passwords = dict(vault_pass='secret')

    # Create the ResultCallback object, used to print info about task status
    results_callback = ResultCallback()

    # create inventory, use path to host config file as source or
    # hosts in a comma separated string
    inventory = InventoryManager(loader=loader, sources='localhost,')

    # Merges all sources of variables
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Playbook to connect to a bssid
    play_source = dict(
        name="Ansible Play",
        hosts='localhost',
        gather_facts='no',
        tasks=[
            # Check for wpa_supplicant file
            dict(action=dict(module='stat', path=wpa_supp_path), \
                    register='wpa_exists'),

            # Exit play if wpa_supplicant is not found
            dict(action=dict(module='debug',\
                    msg='Could not find wpa_supplicant with given ssid'),\
                    when='not wpa_exists.stat.exists'),
            dict(action=dict(module='fail',\
                    msg='Could not find wpa_supplicant for given ssid'),\
                    when='not wpa_exists.stat.exists'),
            dict(action=dict(module='meta', args='end_play'),\
                    when='not wpa_exists.stat.exists'),

            # Take down pscheduler services if in paranoid mode
            dict(action=dict(module='systemd', name='pscheduler-archiver',\
                    state='stopped'), when=flags['pscheduler_restart']),
            dict(action=dict(module='systemd', name='pscheduler-runner',\
                    state='stopped'), when=flags['pscheduler_restart']),
            dict(action=dict(module='systemd', name='pscheduler-scheduler',\
                    state='stopped'), when=flags['pscheduler_restart']),
            dict(action=dict(module='systemd', name='pscheduler-ticker',\
                    state='stopped'), when=flags['pscheduler_restart']),

            # Stop apache if toggled
            dict(action=dict(module='systemd', name='apache2',\
                    state='stopped'), when=flags['apache_restart']),

            # Stop postgres if toggled
            dict(action=dict(module='systemd', name='postgresql',\
                    state='stopped'), when=flags['postgres_restart']),

            # release dhclient lease on `interface`
            dict(action=dict(module='command', args=dhclient_release), \
                    ignore_errors='yes'),

            # Remove default route to make dhclient happy
            dict(action=dict(module='command', args='ip route del default'),\
                    ignore_errors='yes'),

            # Remove WiFi interface config
            dict(action=dict(module='file',\
                    path='/var/run/wpa_supplicant/wlan0', state='absent')),

            # Kill wpa_supplicant
            dict(action=dict(module='command', args='killall wpa_supplicant'),\
                    ignore_errors='yes'),

            # Bring WiFi interface down
            dict(action=dict(module='command', args=bring_down)),

            # Flush WiFi interface config
            dict(action=dict(module='command', args=flush_config)),

            # Bring interface back up
            dict(action=dict(module='command', args=bring_up)),

            # Add SSID to wpa_supplicant
            dict(action=dict(module='lineinfile', path=wpa_supp_path,\
                    regexp='^(.*)ssid=(.*)$', line=ssid_line)),

            # Add BSSID to wpa_supplicant
            dict(action=dict(module='lineinfile', path=wpa_supp_path,\
                    regexp='^(.*)bssid=(.*)$', line=bssid_line)),

            # Connect to WiFi
            dict(action=dict(module='command', args=run_wpa_supplicant)),

            # Get an IP
            dict(action=dict(module='command', args=dhclient)),

            # Bring pScheduler services back
            dict(action=dict(module='systemd', name='pscheduler-archiver',\
                    state='started'), when=flags['pscheduler_restart']),
            dict(action=dict(module='systemd', name='pscheduler-runner',\
                    state='started'), when=flags['pscheduler_restart']),
            dict(action=dict(module='systemd', name='pscheduler-scheduler',\
                    state='started'), when=flags['pscheduler_restart']),
            dict(action=dict(module='systemd', name='pscheduler-ticker',\
                    state='started'), when=flags['pscheduler_restart']),

            # Start apache if toggled
            dict(action=dict(module='systemd', name='apache2',\
                    state='started'), when=flags['apache_restart']),

            # Start postgres if toggled
            dict(action=dict(module='systemd', name='postgresql',\
                    state='started'), when=flags['postgres_restart']),
            ]
        )

    # Create the playbook
    play = Play().load(play_source, variable_manager=variable_manager,\
            loader=loader)

    # Run the playbook
    connected = True
    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
            stdout_callback=results_callback, # Use custom callback method
            )
        result = tqm.run(play)
        if result != 0:
            connected = False
    finally:
        # Clean up child processes
        if tqm is not None:
            tqm.cleanup()

        # Remove ansible tmpdir
        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    # Wait for pscheduler to come back
    if flags['wait_time'] != 0:
        print('Sleeping for', flags['wait_time'])
        time.sleep(flags['wait_time'])

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Check if connection is successful
    if flags['paranoid']:
        connected = bssid_validator.validate_connect(bssid)

    # Get ip
    ni.ifaddresses('wlan0')
    ip_addr = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
    
    connection_info = {}
    connection_info['ssid'] = ssid
    connection_info['bssid'] = bssid
    connection_info['time'] = elapsed_time
    connection_info['new_ip'] = ip_addr
    connection_info['operation'] = 'connection'
    connection_info['connected'] = connected

    json_info = json.dumps(connection_info)

    # Log status of connection
    if connected:
        log_msg = 'Connected: ' + json_info
        syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, log_msg)
    else:
        log_msg = 'Failed to connect: ' + json_info
        syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, log_msg)

    return json_info


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

