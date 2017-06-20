#!/usr/bin/env python
import argparse
import os
import pexpect
import getpass
import imp
from datetime import datetime

try:
    imp.find_module('cli')
    import cli
except ImportError:
    guestshell = False


class csr_cli():
    def __init__(self):
        try:
            imp.find_module('cli')
            self.guestshell = True
        except ImportError:
            self.guestshell = False

    def login(self, hostname, username, password, pem_file):
        if self.guestshell is True:
            return

        if pem_file is not None:
            cmd = "ssh -i %s.pem %s@%s" % (pem_file, username, hostname)
        else:
            cmd = "ssh %s@%s" % (username, hostname)
        self.ssh = pexpect.spawn(cmd)
        ssh_newkey = 'Are you sure you want to continue connecting (yes/no)?'

        ret = self.ssh.expect([pexpect.TIMEOUT, ssh_newkey, '[P|p]assword:'])
        if ret == 0:
            print '[-] Error Connecting to ' + hostname
            return
        if ret == 1:
            self.ssh.sendline('yes')
            ret = self.ssh.expect([pexpect.TIMEOUT, '[P|p]assword:'])
            if ret == 0:
                print '[-] Could not accept new key from ' + hostname
                return
        self.ssh.sendline(password)
        auth = self.ssh.expect(['[P|p]assword:', '>', '#'])
        if auth == 0:
            print 'User password is incorrect'
            return
        if auth == 1:
            print('username and password are correct')

        self.ssh.sendline("terminal length 0")
        self.ssh.expect(['#'])
        self.ssh.sendline("terminal width 120")
        self.ssh.expect(['#'])

        before = self.ssh.before
        before = before[before.rindex('\n') + 1:].lstrip()
        self.prompt = before + self.ssh.after

    def logout(self):
        if self.guestshell is True:
            return
        self.ssh.sendline('exit')

    def upload_file(self, tftp_server_ip, filename, remote_filepath, port=69, directory="/bootflash/"):
        if tftp_server_ip is not None:
            import tftpy

            tftp_options = {}
            tftp_options['blksize'] = 512
            tclient = tftpy.TftpClient(tftp_server_ip, port, tftp_options)
            if remote_filepath is "None":
                remote_filepath = filename
            try:
                tclient.upload(remote_filepath, directory + filename)
            except Exception as e:
                print "Uploading file Failed.  Error: %s" % (e)
                return False
            print "Upload Complete to %s" % (tftp_server_ip)
            return True

    def get_output(self, command):
        if self.guestshell is True:
            cmd_output = cli.execute(command)
        else:
            self.ssh.sendline(command)   # run a command
            self.ssh.expect(self.prompt)
            # print everything before the prompt.
            cmd_output = self.ssh.before.lstrip(command)
            cmd_output = cmd_output.rstrip(self.prompt)

        return cmd_output.replace("\r", "")

    def save_cmd_output(self, cmdlist, filename, directory="/bootflash/", print_output=None):
        if not os.path.exists(directory):
            directory = os.getcwd() + '/'
        print "opening %s" % (directory + filename)
        c = '='
        with open(directory + filename, 'w') as f:
            for command in cmdlist:
                command = command.strip()
                if command not in cmd_list_tech_support:
                # if command in cmd_list_automation:
                    print "%s" % command
                time_before = datetime.now()

                cmd_output = self.get_output(command)
                delta = datetime.now() - time_before
                delta_float = float(delta.seconds) + float(delta.microseconds) / float(1000000)
                # if "Invalid input" in cmd_output:
                #     print "Invalid Command: %s -> %s" % (command, cmd_output)
                #     continue

                command = command[-60:]
                col_space = (80 - (len(command) + 4)) / 2
                total = (col_space * 2) + len(command) + 4 + 2
                diff = (total - 80) + 1
                if print_output is not None:
                    print "\n%s %s %s" % (c * col_space, "cmd: " + command, c * (col_space - diff))
                    print "%s\n%s" % (cmd_output, c * 80)

                f.write("\n%s %s %s\n" %
                        (c * col_space, "cmd: " + command, c * (col_space - diff)))
                f.write("\nCommand took %f seconds\n" %
                        (delta_float))
                f.write("%s\n%s\n" % (cmd_output, c * 80))


cmdlist_general = \
    [
        "show version",
        "show startup-config",
        "show run",
        "show log",
        "show processes cpu platform",
        "show controllers",
        "dir core",
    ]

cmdlist_virtual = \
    [
        "show virtual-service",
        "show virtual-service detail",
        "show virtual-service list",
    ]

cmdlist_interface = \
    [
        "show interfaces",
        "show interfaces accounting",
        "show ip interface",
        "show ip interface brief",
        "show ip route",
    ]

cmdlist_license = \
    [
        "show license",
        "show license detail",
        "show license udi",
        "show license udi history",
    ]

cmdlist_platform_hardware = \
    [
        "show platform hardware qfp active system state",
        "show platform hardware qfp active statistics drop",
        "show platform hardware qfp active feature lic-bw oversubscription detailed",
        "show platform hardware qfp active datapath utilization",
        "show platform hardware throughput level",
        "show platform hardware qfp active infra chipset 0 capabilities",
        "show platform hardware qfp active datapath utilization summary",
        "show platform hardware qfp active datapath infrastructure sw-lsmpi",
        "show platform hardware qfp active datapath infrastructure sw-ipc",
        "show platform hardware qfp active datapath infrastructure sw-dis",
        "show platform hardware qfp active datapath infrastructure sw-cio",
        "show platform hardware qfp active datapath infrastructure sw-nic",
        "show platform hardware qfp active datapath infrastructure sw-pktmem",
        "show platform hardware qfp active datapath infrastructure sw-hqf",
        "show platform hardware qfp active datapath infrastructure time basic",
        "show platform hardware qfp active infra punt statistics type per-cause | exc _0_",
        "show platform hardware qfp active datapath pmd ifdev",
        "show platform hardware qfp active datapath pmd port-config",
        "show platform hardware qfp active datapath pmd system",
        "show platform hardware qfp active datapath ifdev",
        "show dmvpn",
    ]

cmdlist_platform_software = \
    [
        "show platform software vnic-if interface-mapping",
        "show platform software system all",
        "show platform software cpu share",
        "show platform software status control-processor br",
        "show platform software vmem info",
        "show platform software vnic-if ifdev",
    ]

cmd_list_automation = \
    [
        "show platform hardware qfp active infra punt statistics type per-cause | ex _0_",
        "show platform hardware qfp active infra punt statistics type per-cause",
        "show platform hardware qfp active infra chipset 0 cap",
        "show platform hardware qfp active datapath infrastructure sw-lsmpi",
        "show platform hardware qfp active datapath infrastructure sw-ipc",
        "show platform hardware qfp active datapath infrastructure sw-pktmem",
        "show platform hardware qfp active datapath infrastructure time bas",
        "show platform hardware qfp active datapath infrastructure sw-hqf",
        "show platform hardware qfp active datapath infrastructure sw-dis",
        "show platform hardware qfp active datapath infrastructure sw-cio",
        "show platform hardware qfp active datapath infrastructure sw-nic",
        "show platform hardware qfp active statistics drop",
        "show controllers",
        "show platform software status control-processor br",
        "show platform software vmem info",
        "show platform hardware qfp active system state",
        "show platform software vnic-if interface-mapping",
        "show license udi",
        "show license detail",
        "show virtual-service",
        "show virtual-service list",
        "show log",
    ]

cmd_list_tech_support = \
    [

        "show version installed",
        "show version running",


        "show controllers",
        "show interfaces",
        "show interfaces accounting",
        "show ip interface",
        "show ip interface brief",
        "show ip route",

        "show platform hardware qfp active infrastructure punt config cause",
        "show platform hardware qfp active infrastructure punt internal-interface",
        "show platform hardware qfp active interface platform internal0/0/rp:0",
        "show platform hardware qfp active interface platform internal0/0/recycle:0",
        "show platform hardware qfp active interface platform internal0/0/crypto:0",
        "show platform hardware qfp active infrastructure uidb internal0/0/rp:0 input config",
        "show platform hardware qfp active infrastructure uidb internal0/0/recycle:0 input config",
        "show platform hardware qfp active infrastructure uidb internal0/0/rp:0 output config",
        "show platform hardware qfp active infrastructure uidb internal0/0/recycle:0 output config",

        "show platform hardware qfp active infrastructure punt statistics interface 1",
        "show platform hardware qfp active infrastructure punt statistics interface 2",
        "show platform hardware qfp active infrastructure punt statistics interface 3",
        "show platform hardware qfp active infrastructure punt statistics interface 4",
        "show platform hardware qfp active interface platform internal0/0/rp:0 statistics",
        "show platform hardware qfp active interface platform internal0/0/recycle:0 statistics",
        "show platform hardware qfp active infrastructure punt statistics type per-cause",
        "show platform hardware qfp active infrastructure punt statistics type global-drop",
        "show platform hardware qfp active infrastructure punt statistics type punt-drop",
        "show platform hardware qfp active infrastructure punt statistics type inject-drop",

        "show platform hardware qfp active statistics drop",

        "show platform hardware qfp active system state",
        "show platform hardware qfp active system transactions",
        "show platform hardware qfp active datapath infrastructure time basic",
        "show platform hardware qfp active datapath infrastructure sw-lsmpi",
        "show platform hardware qfp active datapath infrastructure sw-ipc",
        "show platform hardware qfp active datapath infrastructure sw-dis",
        "show platform hardware qfp active datapath infrastructure sw-cio",
        "show platform hardware qfp active datapath infrastructure sw-nic",
        "show platform hardware qfp active datapath infrastructure sw-pktmem",
        "show platform hardware qfp active datapath infrastructure sw-hqf",

        "show platform hardware qfp active infrastructure exmem statistics",
        "show platform hardware qfp active infrastructure exmem statistics user",
        "show platform hardware qfp active infrastructure exmem resource",
        "show platform hardware qfp active infrastructure exmem region",
        "show platform hardware qfp active infrastructure exmem table",
        "show platform hardware qfp active infrastructure bqs status",

        "show platform hardware qfp active feature acl control",
        "show platform hardware qfp active feature acl tree",

        "show platform hardware qfp active feature tunnel state",

        "show platform hardware qfp active feature erspan state",
        "show platform hardware qfp active feature erspan session summary",

        "show platform hardware qfp active feature ess state",

        "show platform hardware qfp active feature ipfrag global",

        "show platform hardware qfp active feature lic-bw oversubscription detailed",

        "show platform hardware qfp active infrastructure chipset 0 version",
        "show platform hardware qfp active infrastructure chipset 0 capabilities",

        "show platform hardware qfp active datapath utilization",
        "show platform hardware qfp active datapath utilization summary",

        "show platform hardware qfp active datapath pmd ifdev",
        "show platform hardware qfp active datapath pmd port-config",
        "show platform hardware qfp active datapath pmd system",
        "show platform hardware qfp active datapath ifdev",

        "show platform hardware throughput level",

        "show hw-programmable all",

        "show bootlog FP active",

        "show bootlog RP active",

        "show platform software cpu share",
        "show platform software diagnostic chassis-manager R0 cpld",
        "show platform software diagnostic chassis-manager R0 status",

        "show platform software mount R0 brief",

        "show platform software ipc queue-based chassis-manager R0 connection",
        "show platform software ipc queue-based forwarding-manager R0 connection",

        "show platform software ipc stream-based chassis-manager F0 connection",
        "show platform software ipc stream-based chassis-manager F0 manager",
        "show platform software ipc stream-based chassis-manager R0 connection",
        "show platform software ipc stream-based chassis-manager R0 manager",

        "show platform software ipc stream-based forwarding-manager F0 connection",
        "show platform software ipc stream-based forwarding-manager F0 manager",
        "show platform software ipc stream-based forwarding-manager R0 connection",
        "show platform software ipc stream-based forwarding-manager R0 manager",

        "show platform software ipc stream-based host-manager R0 connection",
        "show platform software ipc stream-based host-manager R0 manager",

        "show platform software ipc stream-based shell-manager R0 connection",
        "show platform software ipc stream-based shell-manager R0 manager",

        "show platform software mount R0",

        "show platform soft object-manager F0 statistic",

        "show platform software peer chassis-manager F0",
        "show platform software peer chassis-manager R0",
        "show platform software peer forwarding-manager F0",
        "show platform software peer forwarding-manager R0",

        "show platform software peer shell-manager",
        "show platform software peer shell-manager brief",

        "show platform software process environment host-manager R0",

        "show platform software process environment shell-manager RP active",

        "show platform software process list R0",
        "show platform software process list R0 summary",

        "show platform software status control-processor br",
        "show platform software system all",
        "show platform software vnic-if ifdev",
        "show platform software vnic-if interface-mapping",
        "show platform software vmem info",

        "show processes cpu platform",
        "show license",
        "show license detail",
        "show license udi",
        "show license udi history",

        "show virtual-service",
        "show virtual-service list",
        "show virtual-service detail",

    ]

cmd_list_ts =  \
    [
        "show tech-support"
    ]

parser = argparse.ArgumentParser(description="Upload test file")
parser.add_argument('--server_ip', '-s',
                    help='The tftp server ip address', default=None)
parser.add_argument('--remote_filename', '-r',
                    help='Filename and path on tftp server', default="None")
parser.add_argument('--filename', '-f',
                    help='Filename and path to upload to tftp server', default="csr-debug.txt")
parser.add_argument(
    '--directory', '-d', help='directory to save file (default=bootflash)', default="/bootflash/")
parser.add_argument('--output', '-o', help='print to stdout', default=None)
parser.add_argument(
    '--ip', '-i', help='ip/hostname to connect to', default=None)
parser.add_argument(
    '--user', '-u', help='username on remote device', default='cisco')
parser.add_argument('--password', '-p',
                    help='password on remote device', default='cisco')
parser.add_argument('--print_output', '-P',
                    help='print to stdout', default=None)
parser.add_argument('--category', '-c',
                    help='category to collect', default=None)
args = parser.parse_args()

csr = csr_cli()

if csr.guestshell is False:
    if args.ip is None:
        hostname = raw_input('hostname: ')
    else:
        hostname = args.ip

    if args.user is None:
        username = raw_input('username: ')
    else:
        username = args.user

    if args.password is None:
        password = getpass.getpass('password: ')
    else:
        password = args.password

    csr.login(hostname, username, password, None)

all_cmd_list = cmdlist_general + cmdlist_interface + cmdlist_license + \
    cmdlist_platform_hardware + cmdlist_platform_software + \
    cmdlist_virtual

if args.category is not None:
    all_cmd_list = cmdlist_general
    if "hardware" in args.category:
        all_cmd_list += cmdlist_platform_hardware
    if "software" in args.category:
        all_cmd_list += cmdlist_platform_software
    if "interface" in args.category:
        all_cmd_list += cmdlist_interface
    if "license" in args.category:
        all_cmd_list += cmdlist_license
    if "automation" in args.category:
        all_cmd_list = cmd_list_automation
    if "techsupport" in args.category:
        all_cmd_list = cmd_list_tech_support

csr.save_cmd_output(all_cmd_list, args.filename,
                    print_output=args.print_output)

csr.logout()

csr.upload_file(args.server_ip, args.filename, args.remote_filename)


# capture log files
# capture core files
# grab tracelogs
# update tech support text file
# check for invalid commands
