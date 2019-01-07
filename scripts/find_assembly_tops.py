#!/usr/bin/env python
# Copyright (c) 2016, The Regents of the University of California (Regents).
# All Rights Reserved. See LICENSE for license details.

# Our goal:
#
# INPUT:
#   - a histogram of PCs and times executed
#   - an objdump file
#
# OUTPUT:
#   - a file of the most frequently-executed assembly code snippets

import optparse
 
# return an array of WHEN there's a gap in the instructions
def find_pc_boundaries(freq_pc_pairs, size):
    last_pc = 0
    i = 0
    boundaries = []
    for freq, pc_str in freq_pc_pairs[:size]:
        pc = int(pc_str, 16)
        #print "%s = %d" % (pc_str, pc)
        if last_pc - 4 != pc:
            #print "Found Boundary at (%d), pc=0x%s" % (i, pc_str)
            boundaries.append((i, pc_str))
        last_pc = pc
        i += 1
    return boundaries


def get_inst_size(pc_string, assembly_dict):
    line = assembly_dict[pc_string]
    bits = line.split('\t')[0].split()
#    print line,"-bits[",bits,"]len(b[0])=",len(bits[0]),"len(bits)=",len(bits)
    size = len(bits[0])*len(bits)/2
    # check in x86 for wrap-around!
    if size == 7:
        pc = int(pc_string, 16)
        npc = pc + size
        npc_string = "%x" % (npc)
        nextline = assembly_dict[npc_string]
        if nextline.count('\t') == 0:
            # it's a partial line
            bits = nextline.split()
            size += len(bits[0])*len(bits)/2
    return size


def find_hot_codes(freq_pc_pairs, total_insts, max_cdf, dumpfile):
    d = open(dumpfile)
    dump_pc_assembly_pairs = [l.strip().split(':\t') for l in d.readlines() if ':\t' in l]
    assembly_dict = dict(dump_pc_assembly_pairs)


    last_pc = 0
    pc_group = []
    this_cdf = 0.
    total_cdf = 0.
    this_inst_count = 0
    this_freq = 0
    found_segments = 0 
    partial_line = False # skip an iteration if a long x86 instruction wrapped onto the next line
    for freq, pc in freq_pc_pairs[:]:
        if partial_line:
            partial_line = False
            continue
        pc_value = int(pc, 16)
        if not pc in assembly_dict:
            print pc,"\tline not found"
            last_pc = pc_value
            this_cdf += 100.*freq/total_insts
            total_cdf += 100.*freq/total_insts
            this_freq += freq
            this_inst_count += 1
            continue
        sz = get_inst_size(pc, assembly_dict)
        if sz > 7:
            partial_line = True
#            print "Super line: ", assembly_dict[pc]

#        print "----------------: 0x",pc,"-(0d",pc_value,")",freq,"- sz=",sz,"|| last_pc=",last_pc

        if pc_value +sz != last_pc and last_pc != 0:
            print "\n-------- Segment %d CDF= %5.2f %%, Total CDF= %5.2f %% (%d instructions, %6.3f B total) --------" % \
                (found_segments, this_cdf, total_cdf, this_inst_count, float(this_freq)/1.0e9)
            for p in reversed(pc_group):
                line = assembly_dict[p]
                print p, "\t", line.split('\t',1)[1]
            pc_group = []
            this_cdf = 0.
            this_freq = 0
            this_inst_count = 0
            found_segments += 1
#            if found_segments >= num_segments:
            if total_cdf > float(max_cdf):
                return

        pc_group.append(pc)
        last_pc = pc_value
        this_cdf += 100.*freq/total_insts
        total_cdf += 100.*freq/total_insts
        this_freq += freq
        this_inst_count += 1
     

def main():
    parser = optparse.OptionParser()
    parser.add_option('-f', '--histogram', dest='histogram_file',
                    help='input histogram file')
    parser.add_option('-d', '--objdump', dest='objdump_file',
                    help='input objdump file')
    parser.add_option('-n', '--lines', dest='lines',
                    help='CDF number of top lines to analyze', default=40)
    parser.add_option('-s', '--segments', dest='segments',
                    help='CDF number of top segments to analyze', default=20)
    (options, args) = parser.parse_args()
    if not options.histogram_file or not options.objdump_file:
        parser.error('Please give input filenames with -f and -d')
    num_to_print = int(options.lines)
    h = open(options.histogram_file)

    # sanitize for header, footer
    hlines = map(lambda l: l.split(), h.readlines()[1:-4])

    freq_pc_pairs = map(lambda l: (int(l[1]), l[0]), hlines)
    total_insts = sum(map(lambda p: p[0], freq_pc_pairs))

    freq_pc_pairs.sort(reverse=True)
    cdf_sum = 0.
    count = 0
    for freq, pc in freq_pc_pairs[:]:
        percent = 100.*freq/total_insts
        count += 1
        cdf_sum += percent
        print '%8s %12u %8.3f%% %8.3f%%' % (pc, freq, percent, cdf_sum)
        if cdf_sum > num_to_print or count > 5000:
            break
    print 'Total:%15u, Number printed:%d' % (total_insts, count)

 
    find_hot_codes(freq_pc_pairs, total_insts, float(options.segments), options.objdump_file)


if __name__ == '__main__':
  main()
