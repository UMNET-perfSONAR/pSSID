import subprocess

def validate_connect(address):
    p = subprocess.Popen(['iwgetid', '-a'], stdout=subprocess.PIPE)

    output,_= p.communicate()

    # Check for not connected return
    if str(output) == "b''":
        return False

    mac_address = str(output).split()[3]
    mac_address = mac_address[0:17]

    if address == mac_address:
        print(mac_address)
        return True

    return False

