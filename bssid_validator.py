import subprocess

def validate_connect(address):
    p = subprocess.Popen(['iwgetid', '-a'], stdout=subprocess.PIPE)

    output, err = p.communicate()
    rc = p.returncode

    mac_address = str(output).split()[3]
    mac_address = mac_address[0:17]

    if address == mac_address:
        print(mac_address)
        return True

    return False

