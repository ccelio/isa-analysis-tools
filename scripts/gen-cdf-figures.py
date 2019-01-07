#!/usr/bin/env python
# Copyright (c) 2016, The Regents of the University of California (Regents).
# All Rights Reserved. See LICENSE for license details.

import matplotlib
matplotlib.use('PDF') # must be called immediately, and before import pylab
                      # sets the back-end for matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pylab
import optparse

DIR="data-riscv64gc-o3-strict-aliasing"
full_bmarks=["400.perlbench", "401.bzip2", "403.gcc", "429.mcf", "445.gobmk", "456.hmmer", "458.sjeng", "462.libquantum", "464.h264ref", "471.omnetpp", "473.astar", "483.xalancbmk"]

bmarks=["perlbench", "bzip2", "gcc", "mcf", "gobmk", "hmmer", "sjeng", "libquantum", "h264ref", "omnetpp", "astar", "xalancbmk"]
num_workloads=[3,6,9,1,5,2,1,1,3,1,2,1]
FAST=False

     
cmap = matplotlib.pyplot.get_cmap("viridis_r")
print dir(cmap)

max_colors = 13
color_intensities = [float(x)/(max_colors-1) for x in range(max_colors)]
vircol = [matplotlib.cm.viridis(c) for c in color_intensities]


def getColor(idx, maxidx):
    val = ((idx)*max_colors/maxidx) % max_colors
    print "i:",idx,"m:",maxidx," -> ",val
    return vircol[val]


def geomean(nums):
    return (reduce(lambda x, y: x*y, nums))**(1.0/len(nums))
 

def plot_cdf(plotter, bname, cdf, boundaries, idx, work_id, max_work):
    plt.title(bname, y=0.95)
    num_points = 100
    plotter.plot(range(0,num_points), cdf[:num_points], color=getColor(work_id, max_work)) #, marker='.' )
    plotter.set_ylabel("CDF %")
    plotter.xaxis.labelpad = 1 

    # only put x-label if last row
    if idx >= 11:
        plotter.set_xlabel("Instruction Number")
    ymin,ymax = plt.ylim()
    plt.ylim([0,100])
    plt.xlim([0,100])

    plt.gca().yaxis.grid(True)
    plt.gca().set_axisbelow(True)

    x = [i for (i,pc) in boundaries]
    y = [cdf[i] for i in x]
    plotter.plot(x,y, marker='.', markersize='3.8', color=getColor(work_id, max_work), linestyle='none')

#    y = 5
#    for x, pc in boundaries:
#        if x > num_points:
#            break    
#        plotter.axvline(x, linewidth=0.9, color="grey")
##        plotter.text(x, y, pc)
#        y = (y + 1) % 30


# return an array of WHEN there's a gap in the instructions
def find_pc_boundaries(freq_pc_pairs, size):
    last_pc = 0
    i = 0
    boundaries = []
    for freq, pc_str in freq_pc_pairs[:size]:
        pc = int(pc_str, 16)
        #print "%s = %d" % (pc_str, pc)
        if last_pc - 4 != pc and last_pc - 2 != pc:
            #print "Found Boundary at (%d), pc=0x%s" % (i, pc_str)
            boundaries.append((i, pc_str))
        last_pc = pc
        i += 1
    return boundaries
            
        
def main():

    # Plotting
    fig = plt.figure(figsize=(7.2,2.5))
 
    font = {#'family' : 'normal',
#            'weight' : 'bold',
            'size'   : 8}
    matplotlib.rc('font', **font)
    cmap = matplotlib.pyplot.get_cmap("viridis")
    print "Cmap Number: ", cmap.N
  
    NUM_FIGS = len(bmarks)
#    assert (NUM_FIGS == 12)
    fig = plt.figure(figsize=(7.1,8.5))
    fig.subplots_adjust(bottom=0.05, top=.95, left=0.08, right=0.96)

    x = 0
    for bname in bmarks:
        x += 1 
        if NUM_FIGS == 1:
            p = fig.add_subplot(1,1,x)
        else:
            p = fig.add_subplot(NUM_FIGS/2,2,x)
        fig.subplots_adjust(hspace=.5)

        print "Bname  : ", bname
#        print "w      : ", num_workloads[x-1]

        for w in range(num_workloads[x-1]):
            fname = "./" + DIR + "/" + bname + "." + str(w) + ".err"
            print "Opening: ", fname
             
            # sanitize for header, footer
            f = open(fname)
            lines = map(lambda l: l.split(), f.readlines()[1:-4])

            freq_pc_pairs = map(lambda l: (int(l[1]), l[0]), lines)
            total_insts = sum(map(lambda p: p[0], freq_pc_pairs))

#            print "Total Instructions: ", total_insts

            freq_pc_pairs.sort(reverse=True)
            cdf_sum = 0.
            i = 0
            num_to_print = len(freq_pc_pairs)
            if num_to_print > 1000:
                num_to_print = 1000
#            print "num_to_print:", num_to_print
            cdf_array = [None] * num_to_print
            for freq, pc in freq_pc_pairs[:num_to_print]:
                percent = 100.*freq/total_insts
                cdf_array[i] = cdf_sum
                i += 1
                cdf_sum += percent
    #            print '%8s %12u %8.3f%% %8.3f%%' % (pc, freq, percent, cdf_sum)
    #        print 'Total:%15u' % total_insts

            # Plotting
#            print "Computing Boundaries"
            boundaries = []
            if not FAST:
                boundaries = find_pc_boundaries(freq_pc_pairs, num_to_print)
#            print "Plotting CDF"
            plot_cdf(p, full_bmarks[x-1], cdf_array, boundaries, x, w, num_workloads[x-1])
            if FAST:
                break
     

    gname = "./graphs/cdfs.pdf"
    plt.savefig(gname)
    print ("Saving plot at : " + gname)
 

if __name__ == '__main__':
  main()
