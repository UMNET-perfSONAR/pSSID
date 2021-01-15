import subprocess
import re
import pika
import time
import traceback
import json
import netifaces as ni

def rabbitmqQueue(message, queue_name ="", routing_key = "", exchange_name = ""):
    url = "amqp://elastic:elastic@pssid-elk.miserver.it.umich.edu"
    try:
        connection = pika.BlockingConnection(pika.URLParameters(url))
        channel=connection.channel()
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message)
        connection.close()
    except:
        print(time.ctime(time.time()))
        print("ERROR in archiving with rabbitmqQueue")
        print(traceback.print_exc())


def get_ip(interface):
    ip_addr = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
    return ip_addr


def cpu_info():
    cpuinfo = {}
    info = subprocess.check_output("cat /proc/cpuinfo", shell=True).strip()
    info = info.decode()
    cpuinfo['hardware'] = re.search("Hardware.*", info).group().split()[-1]
    cpuinfo['revision'] = re.search("Revision.*", info).group().split()[-1]
    cpuinfo['serial'] = re.search("Serial.*", info).group().split()[-1]
    cpuinfo['model'] = re.search("Model.*", info).group().split(":")[-1].strip()
    return cpuinfo


def os_info():
    osinfo = {}
    info = subprocess.check_output("hostnamectl", shell=True).strip()
    info = info.decode()
    osinfo['hostname'] = re.search("hostname.*", info).group().split(":")[-1].strip()
    osinfo['os'] = re.search("System.*", info).group().split(":")[-1].strip()
    osinfo['kernel'] = re.search("Kernel.*", info).group().split(":")[-1].strip()
    return osinfo


def replaceIp(new_ip):
    file_obj = open('/usr/local/bin/pssid/pssid_conf.json', 'r')
    pssid_dict = json.loads(file_obj.read())
    pssid_dict['meta_information']['probe_stats']['probe_ipv4'] = new_ip
    file_obj = open('/usr/local/bin/pssid/pssid_conf.json', 'w')
    file_obj.write(json.dumps(pssid_dict, indent=4))


def main():
    cpuinfo = cpu_info()
    osinfo = os_info()

    message = {
        'operation': 'registration',
        'eth0_ipv4': get_ip('eth0'),
        'hardware': cpuinfo['hardware'],
        'revision': cpuinfo['revision'],
        'serial': cpuinfo['serial'],
        'model': cpuinfo['model'],
        'hostname': osinfo['hostname'],
        'os': osinfo['os'],
        'kernel': osinfo['kernel']
    }

    rabbitmqQueue(json.dumps(message), "pSSID", "pSSID")
    replaceIp(message['eth0_ipv4'])


if __name__ == '__main__':
    main()
    exit(0)
