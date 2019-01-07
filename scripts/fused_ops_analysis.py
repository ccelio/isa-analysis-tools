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
#   - the number of dynamic bytes fetched (well, committed, but whatever).
#   - the number of "macro-ops" committed (aka, instructions executed, but
#       fused-ops only count as one), 
#   - the number of fused macro-ops
#   - the number of "slli 30; srli 30" garbage due to uint32_t in RV64
#   - only counts instructions executed in the objdump (aka, no bbl or vmlinux).

import optparse
 

def get_inst_size(pc_string, assembly_dict):
    if pc_string not in assembly_dict:
        #print "PC (0x",pc_string,") not found!"
        return 4
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
#            print "Bits:"
#            print bits
#            print "    size =",size
    return size

def last_inst_was_adjacent(pc, last_pc):
    return pc+2 == last_pc or pc+4 == last_pc
    # only works for RISC-V
    # check if it's either +2 or +4. if it's either, we're good.
#    print "pc:",pc, ", last:",last_pc," - retval:",retval

     
def get3OpTypeInst(pc, asm_dict):
    instruction = asm_dict[pc].split('\t')
    if len(instruction) != 3:
        return None
    operands = instruction[2].split(',')
    if len(operands) != 3:
        return None
    typ = instruction[1]
    rd  = operands[0]
    rs1 = operands[1]
    imm = operands[2]
    return (typ, rd, rs1, imm)

# e.g., loads
def get2OpTypeInst(pc, asm_dict):
    instruction = asm_dict[pc].split('\t')
    if len(instruction) != 3:
        return None
    operands = instruction[2].split(',')
    if len(operands) != 2:
        return None
    typ = instruction[1]
    rd  = operands[0]
    addr = operands[1]
    return (typ, rd, addr)

def isShiftClearUpperIdiom(pc1, pc2, asm_dict):
    if not pc1 in asm_dict or not pc2 in asm_dict:
        return False
    inst = get3OpTypeInst(pc1, asm_dict)
    if inst:
        (typ_1, rd_1, rs1_1, imm_1) = inst
        if typ_1 == "slli" and imm_1 == "0x20":
            inst_1 = inst
            inst = get3OpTypeInst(pc2, asm_dict)
            if inst:
                (typ_2, rd_2, rs1_2, imm_2) = inst
                if typ_2 == "srli" and rd_1 == rd_2 and rd_1 == rs1_2 and \
                          (imm_2 == "0x20" or imm_2 == "0x1e" or imm_2 == "0x1d"):
#                          (imm_2 == "0x20" or imm_2 == "0x1e" or imm_2 == "0x1d" or imm_2 == "0x1c"):
#                    print "PC:",pc1,"- inst1:",inst_1, "   inst2:",inst
                    return True
    return False

def isLoad(typ):
    if len(typ) > 1:
        t = typ[0:2]
        return t == "ld" or t == "lw" or t == "lb" or t == "lh"
    return False
 
def isIdxLoadIdiom(pc1, pc2, asm_dict):
    if not pc1 in asm_dict or not pc2 in asm_dict:
        return False
    inst = get3OpTypeInst(pc1, asm_dict)
    if inst:
        (typ_1, rd_1, rs1_1, rs2_1) = inst
        if (typ_1 == "add" or typ_1 == "addi"): # and rd_1 == rs1_1:
            inst_1 = inst
            inst = get2OpTypeInst(pc2, asm_dict)
            if inst:
                (typ_2, rd_2, address) = inst
                if isLoad(typ_2) and rd_1 == rd_2 and '0(' in address and rd_1 in address:
#                    print "IDX: PC:",pc1,"- inst1:",inst_1, "   inst2:",inst
                    return True
    return False
             
def isIdxLoadIdiomWithConst(pc1, pc2, asm_dict):
    if not pc1 in asm_dict or not pc2 in asm_dict:
        return False
    inst = get3OpTypeInst(pc1, asm_dict)
    if inst:
        (typ_1, rd_1, rs1_1, rs2_1) = inst
        if (typ_1 == "add" or typ_1 == "addi"): # and rd_1 == rs1_1:
            inst_1 = inst
            inst = get2OpTypeInst(pc2, asm_dict)
            if inst:
                (typ_2, rd_2, address) = inst
                if isLoad(typ_2) and rd_1 == rd_2 and not '0(' in address and rd_1 in address:
#                    print "ILC: PC:",pc1,"- inst1:",inst_1, "   inst2:",inst
                    return True
    return False
             
def isLeaIdiom(pc1, pc2, asm_dict):
#    debug = False
    #if pc1 == "35014":
    #    debug = True
    #    print asm_dict[pc1]
    #    print asm_dict[pc2]
    if not pc1 in asm_dict or not pc2 in asm_dict:
        return False
    inst = get3OpTypeInst(pc1, asm_dict)
    if inst:
        (typ_1, rd_1, rs1_1, imm) = inst
#        if typ_1 == "slli" and rd_1 == rs1_1 and (imm == "0x1" or imm == "0x2" or imm == "0x3" or imm == "0x4"):
        if typ_1 == "slli" and (imm == "0x1" or imm == "0x2" or imm == "0x3" or imm == "0x4"):
            inst_1 = inst
            inst = get3OpTypeInst(pc2, asm_dict)
            if inst:
                (typ_2, rd_2, rs1_2, rs2_2) = inst
                if typ_2 == "add" and rd_1 == rd_2 and rd_1 == rs1_2:
#                    print "LEA: PC:",pc1,"- inst1:",inst_1, "   inst2:",inst
                    return True
    return False

 

# freq_pc_pair is sorted at "most-executed" to least executed 
# aka, it's reversed program order, if you will
def find_idiom_count(asm_dict, freq_pc_pairs):

    last_f = 0
    last_pc = "0"
    clr_upper_count = 0
    idx_ld_count = 0
    idx_ldc_count = 0
    lea_count = 0

    for (f, pc) in freq_pc_pairs:
        if last_inst_was_adjacent(int(pc,16), int(last_pc,16)):
            if isShiftClearUpperIdiom(pc, last_pc, asm_dict):
                clr_upper_count += f
            if isIdxLoadIdiom(pc, last_pc, asm_dict):
                idx_ld_count += f
            if isIdxLoadIdiomWithConst(pc, last_pc, asm_dict):
                idx_ldc_count += f
            if isLeaIdiom(pc, last_pc, asm_dict):
                lea_count += f
        last_f = f
        last_f = f
        last_pc = pc

    return (clr_upper_count, idx_ld_count, idx_ldc_count, lea_count)




def main():
    parser = optparse.OptionParser()
    parser.add_option('-f', '--histogram', dest='histogram_file',
                    help='input histogram file')
    parser.add_option('-d', '--objdump', dest='objdump_file',
                    help='input objdump file')
    parser.add_option('-n', '--lines', dest='lines',
                    help='CDF number of top lines to print', default=40)
    parser.add_option('-c', '--compressed', dest='compressed',
                    help='Compress the printout', default=False)
    (options, args) = parser.parse_args()
    if not options.histogram_file or not options.objdump_file:
        parser.error('Please give input filenames with -f and -d')
    num_to_print = int(options.lines)
    h = open(options.histogram_file)

    # sanitize for header, footer
    hlines = map(lambda l: l.split(), h.readlines()[1:-4])

    if not hlines:
        print "%s is empty. Exiting." % (options.histogram_file)
        return

    freq_pc_pairs = map(lambda l: (int(l[1]), l[0]), hlines)
    total_insts = sum(map(lambda p: p[0], freq_pc_pairs))

    freq_pc_pairs.sort(reverse=True)
    cdf_sum = 0.
    count = 0
    for freq, pc in freq_pc_pairs[:num_to_print]:
        percent = 100.*freq/total_insts
        count += 1
        cdf_sum += percent
#        print '%8s %12u %8.3f%% %8.3f%%' % (pc, freq, percent, cdf_sum)
#    print 'Total:%15u, Number printed:%d' % (total_insts, count)


    d = open(options.objdump_file)
    dump_pc_assembly_pairs = [l.strip().split(':\t') for l in d.readlines() if ':\t' in l]
    assembly_dict = dict(dump_pc_assembly_pairs)


    total_insts_not_in_program = sum([f for (f,pc) in freq_pc_pairs if not pc in assembly_dict])

    total_bytes = sum([f*get_inst_size(pc, assembly_dict) for (f,pc) in freq_pc_pairs if pc in assembly_dict])
    total_insts = sum([f                                  for (f,pc) in freq_pc_pairs if pc in assembly_dict])

    (num_clrup, num_idxld, num_idxld_c, num_lea) = find_idiom_count(assembly_dict, freq_pc_pairs)
    total_macroops = total_insts - num_idxld - num_clrup - num_idxld_c - num_lea


    if options.compressed:
        print "%12u\t%13u\t%12u\t%12u\t%12u\t%12u\t%6.3f" % \
            (total_insts, total_bytes, num_idxld, num_idxld_c, num_clrup, num_lea, 100.*total_macroops/total_insts)
        return

    print "====================================================="
    print "Number Insts Not in Pro: %12u bytes" % (total_insts_not_in_program)
    print "%% Not in Program      : %6.3f%%" % \
        (sum([(100.*f/total_insts) for (f,pc) in freq_pc_pairs if not pc in assembly_dict]))

    
    print "------- Stats for instructions in objdump file ---------"
    print "Total Instructions      : %12u instructions" % (total_insts)
    print "Total Dynamic Bytes     : %12u bytes" % (total_bytes)
    print "Average Instruction Size: %6.3f bytes" % (float(total_bytes)/total_insts)

    print "Number of  IdxLoads     : %12u " % (num_idxld)
    print "Percent of IdxLoads     : %6.3f %%" % (100.*num_idxld/total_insts)
    print "Number of SLLI/SRL-30s  : %12u " % (num_clrup)
    print "Percent of SLLI/SRL-30s : %6.3f %%" % (100.*num_clrup/total_insts)
    print "Number of  LEAs         : %12u " % (num_lea)
    print "Percent of LEAs         : %6.3f %%" % (100.*num_lea/total_insts)
    print "Total Macro-ops         : %12u instructions" % (total_macroops)
    print "Fraction of Macops/Inst : %6.3f %%" % (100.*total_macroops/total_insts)
                                                               

if __name__ == '__main__':
  main()
