#!/usr/bin/python
# df_parse - A script to parse a (NTAP) df command to determine filesystem size
# -- Adam Fox (adam.fox@rubrik.com)
#
import sys
import getopt


class Df():
    def __init__(self, name, vserver, total, used, avail,space_flag):
        self.name = name
        if space_flag is True:
            self.total = total
            self.vserver = vserver
            self.used = used
            self.avail = avail
            self.total_bytes = convert_to_bytes(total)
            self.used_bytes = convert_to_bytes(used)
            self.avail_bytes = convert_to_bytes(avail)
        else:
            self.iused = used
            self.iavail = avail

    def is_volume (self, name, vs):
        return (self.name == name and self.vserver == vs)

    def add_inodes (self, used, avail):
        self.iused = used
        self.iavail = avail

    def dump (self):
        try:
            self.name
        except AttributeError:
            print "name = undef"
        else:
            print "name: " + self.name
        try:
            self.total
        except AttributeError:
            print "total - undef"
        else:
            print "total: " + self.total
        try:
            self.used
        except AttributeError:
            print "used = undef"
        else:
            print "used:" + self.used
        try:
            self.iused
        except AttributeError:
            print "iused = undef"
        else:
            print "iused: " + self.iused
        try:
            self.iavail
        except AttributeError:
            print "iavail = undef"
        else:
            print "iavail: " + self.iavail


def convert_to_bytes(val_s):
    val = int(val_s[:-2])
    unit = val_s[-2:]
    if unit == "KB":
        return (val * 1024)
    elif unit == "MB":
        return (val * 1024 * 1024)
    elif unit == "GB":
        return (val * 1024 * 1024 * 1024)
    elif unit == "TB":
        return (val * 1024 * 1024 * 1024 * 1024)
    elif unit == "PB":
        return (val * 1024 * 1024 * 1024 * 1024 * 1024)
    else:
        sys.stderr.write("Unrecognized Unit : " + unit)
        exit(1)

def convert_from_bytes (val):
    if val < 1024:
        return (val, "B")
    if val >= 1024 and val < 104876:
        return (val/1024, "KB")
    if val >= 104876 and val < 1073741824:
        return (val/1024/1024, "MB")
    if val >= 1073741824 and val < 1099511627776:
        return (val/1024/1024/1024, "GB")
    if val >= 1099511627776 and val < 1125899906842624:
        return (val/1024/1024/1024/1024, "TB")
    if val >= 1125899906842624:
        return (val/1024/1024/1024/1024/1024, "PB")


vol_list = []
vol_name = ''
total_bytes = 0
used_bytes = 0
avail_bytes = 0
total_inodes = 0
used_inodes = 0
avail_inodes = 0
df_type = "space"
done = False
p = 1
optlist, args = getopt.getopt(sys.argv[1:], 'ht:', ["help", "type="])
for opt, a in optlist:
    if opt in ('-t', '--type'):
        df_type = a
    if opt in ('-h', '--help'):
        print "HELP"
while (done is False):
    if p == 1:
        fp = open(args[0])
    else:
        fp = open(args[1])
    lines = fp.read().split('\n')
    fp.close()
    parse_next_line = False

    for l in lines:
        lf = l.split()
        if len(lf) == 0:
            continue
        if lf[0].endswith('.snapshot'):
            continue
        if lf[0].startswith('/vol/') is False and parse_next_line is False:
            continue
        if lf[0] == "/vol/vol0/":
            continue
        if len(lf) == 1:
             parse_next_line = True
             vol_name = lf[0]
             continue
        if parse_next_line is False:
            start = 1
            vol_name = lf[0]
        else:
            start = 0
        if df_type == "space" or (df_type == "both" and p == 1):
            vol_list.append(Df(vol_name, lf[start + 5], lf[start], lf[start+1], lf[start+2], True))
        elif df_type == "files":
            vol_list.append(Df(vol_name, lf[start + 4], '', lf[start], lf[start+1], False))
        elif df_type == "both" and p == 2:
            v_index = 0
            found = False
            while found is False:
                if vol_list[v_index].is_volume(vol_name, lf[start + 4]):
                    found = True
                else:
                    v_index += 1
            vol_list[v_index].add_inodes(lf[start], lf[start+1])
        parse_next_line = False
    if df_type == "both" and p == 1:
         p += 1
    else:
        done = True
for vol in vol_list:
    if df_type == "space":
        print vol.name + "," + vol.total + "," + vol.used + "," + vol.avail
        total_bytes += vol.total_bytes
        used_bytes += vol.used_bytes
        avail_bytes += vol.avail_bytes
    elif df_type == "files":
        print vol.name + "," + vol.iused + "," + vol.iavail
        used_inodes += int(vol.iused)
        avail_inodes += int(vol.iavail)
    elif df_type == "both":
        print vol.name + "," + vol.total + "," + vol.used + "," + vol.avail + "," + vol.iused + "," + vol.iavail
        total_bytes += vol.total_bytes
        used_bytes += vol.used_bytes
        avail_bytes += vol.avail_bytes
        used_inodes += int(vol.iused)
        avail_inodes += int(vol.iavail)
print ""
if df_type == "space" or df_type == "both":
    (all_total, all_total_unit) = convert_from_bytes(total_bytes)
    (all_used, all_used_unit) = convert_from_bytes(used_bytes)
    (all_avail, all_avail_unit) = convert_from_bytes(avail_bytes)
if df_type == "space":
    print "Total:," + str(all_total) + all_total_unit + "," + str(all_used) + all_used_unit + "," + str(all_avail) + all_avail_unit
elif df_type == "files":
    print "Total:," + str(used_inodes) + "," + str(avail_inodes)
elif df_type == "both":
        print "Total:," + str(all_total) + all_total_unit + "," + str(all_used) + all_used_unit + "," + str(all_avail) + all_avail_unit + "," + str(used_inodes) + "," + str(avail_inodes)
