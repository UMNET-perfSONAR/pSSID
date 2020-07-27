"""
Connect to an input SSID on an input BSSID
"""

import json
import netifaces as ni
import shutil
import time
import bssid_validator
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C
import syslog


DEBUG = False


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        host = result._host
        if DEBUG:
            print(json.dumps({host.name: result._result}, indent=4))



def prepare_connection(ssid, bssid, interface, auth):
    """
    Prepare a connection to a given ssid and bssid using wpa_supplicant
    Configure and connect on given interface
    Decide connect method and config file based on auth
    """
    connect_msg = "Connecting to " + ssid + " on " + bssid
    syslog.syslog(syslog.LOG_LOCAL3 | syslog.LOG_INFO, connect_msg)

    paranoid = False
    apache_restart = False
    postgres_restart = False
    wait_time = 0

    start_time = time.time()

    # Determine auth method
    if auth['type'] == 'MacAddress':
        print('Connect to MSetup')
        exit()

    elif auth['type'] == 'User':
        wpa_supp_path = '/etc/wpa_supplicant/wpa_supplicant_' + ssid + '.conf'
        print('User auth')

    # Format SSID and BSSID for wpa supplicant
    ssid_line = '    ssid="' + ssid + '"'
    bssid_line = '    bssid=' + bssid 

    # Add interface to ip commands
    bring_down = ('ip link set ' + interface + ' down')
    flush_config = ('ip addr flush dev ' + interface)
    bring_up = ('ip link set ' + interface + ' up')

    # Add interface to wpa supplicant and dhclient commands
    run_wpa_supplicant = ('wpa_supplicant -B -c ' + wpa_supp_path + ' -i ' + interface)
    dhclient = ('dhclient ' + interface)

    # since the API is constructed for CLI it expects certain options to always be set in the context object
    context.CLIARGS = ImmutableDict(connection='local', module_path=['/to/mymodules'], forks=10, become=None, become_method=None, become_user=None, check=False, diff=False)

    # initialize needed objects
    loader = DataLoader() # Takes care of finding and reading yaml, json and ini files
    passwords = dict(vault_pass='secret')

    # Instantiate our ResultCallback for handling results as they come in. Ansible expects this to be one of its main display outlets
    results_callback = ResultCallback()

    # create inventory, use path to host config file as source or hosts in a comma separated string
    inventory = InventoryManager(loader=loader, sources='localhost,')

    # variable manager takes care of merging all the different sources to give you a unified view of variables available in each context
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Playbook to connect to a bssid
    play_source =  dict(
            name = "Ansible Play",
            hosts = 'localhost',
            gather_facts = 'no',
            tasks = [

                # Check for wpa_supplicant file
                dict(action=dict(module='stat', path=wpa_supp_path), register='wpa_exists'),
                
                # Exit play if wpa_supplicant is not found
                dict(action=dict(module='debug', msg='Could not find wpa_supplicant with given ssid'), when='not wpa_exists.stat.exists'),
                #dict(action=dict(module='fail', msg='Could not find wpa_supplicant for given ssid'), when='not wpa_exists.stat.exists'),
                dict(action=dict(module='meta', args='end_play'), when='not wpa_exists.stat.exists'),

                # Take down pscheduler services if in paranoid mode
                dict(action=dict(module='systemd', name='pscheduler-archiver', state='stopped'), when=paranoid),
                dict(action=dict(module='systemd', name='pscheduler-runner', state='stopped'), when=paranoid),
                dict(action=dict(module='systemd', name='pscheduler-scheduler', state='stopped'), when=paranoid),
                dict(action=dict(module='systemd', name='pscheduler-ticker', state='stopped'), when=paranoid),

                # Stop apache if toggled
                dict(action=dict(module='systemd', name='apache2', state='stopped'), when=apache_restart),

                # Stop postgres if toggled
                dict(action=dict(module='systemd', name='postgresql', state='stopped'), when=postgres_restart),

                # Remove default route to make dhclient happy
                dict(action=dict(module='command', args='ip route del default'), ignore_errors='yes'),

                # Remove WiFi interface config
                dict(action=dict(module='file', path='/var/run/wpa_supplicant/wlan0', state='absent')),

                # Kill wpa_supplicant
                dict(action=dict(module='command', args='killall wpa_supplicant'), ignore_errors='yes'),

                # Kill dhclient
                #dict(action=dict(module='command', args='killall dhclient'), ignore_errors='yes'),

                # Bring WiFi interface down
                dict(action=dict(module='command', args= bring_down)),

                # Flush WiFi interface config
                dict(action=dict(module='command', args=flush_config)),

                # Bring interface back up
                dict(action=dict(module='command', args= bring_up)),

                # Add SSID to wpa_supplicant
                dict(action=dict(module='lineinfile', path=wpa_supp_path, regexp='^(.*)ssid=(.*)$', line=ssid_line)),

                # Add BSSID to wpa_supplicant
                dict(action=dict(module='lineinfile', path=wpa_supp_path, regexp='^(.*)bssid=(.*)$', line=bssid_line)),

                # Connect to WiFi
                dict(action=dict(module='command', args=run_wpa_supplicant)),

                # Get an IP
                dict(action=dict(module='command', args=dhclient)),

                # Bring pScheduler services back
                dict(action=dict(module='systemd', name='pscheduler-archiver', state='started'), when=paranoid),
                dict(action=dict(module='systemd', name='pscheduler-runner', state='started'), when=paranoid),
                dict(action=dict(module='systemd', name='pscheduler-scheduler', state='started'), when=paranoid),
                dict(action=dict(module='systemd', name='pscheduler-ticker', state='started'), when=paranoid),

                # Start apache if toggled
                dict(action=dict(module='systemd', name='apache2', state='started'), when=apache_restart),

                # Start postgres if toggled
                dict(action=dict(module='systemd', name='postgresql', state='started'), when=postgres_restart),

                # Restart resolver
                #dict(action=dict(module='systemd', state='restarted', name='systemd-resolved'))
             ]
        )

    # Create the playbook
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # Run the playbook
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  passwords=passwords,
                  stdout_callback=results_callback,  # Use our custom callback instead of the ``default`` callback plugin, which prints to stdout
              )
        result = tqm.run(play) # most interesting data for a play is actually sent to the callback's methods
    finally:
        # we always need to cleanup child procs and the structures we use to communicate with them
        if tqm is not None:
            tqm.cleanup()

        # Remove ansible tmpdir
        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    # Wait for pscheduler to come back
    if wait_time != 0:
        print('Sleeping for', wait_time)
        time.sleep(wait_time)
    
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Check if connection is successful
    connected = bssid_validator.validate_connect(bssid)

    # Get ip
    ni.ifaddresses('wlan0')
    ip = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']

    connection_info = {}
    connection_info['ssid'] = ssid
    connection_info['bssid'] = bssid
    connection_info['time'] = elapsed_time
    connection_info['new_ip'] = ip
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

