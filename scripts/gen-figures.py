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
import sys


# Total Dynamic Bytes (-O3)
dynamic_bytes_data = {
'RV64G': (9787613009464,12026619976548,5253213290312,1107296497700,7787857542508,11716023911916,11489441645752,5462366668348,19365586110024,2314291041560,3747678114072,3961024942240),
'RV64GC':(7386771139900,9271905473172,3660416381884,831532911966,5787043439752,9361603319380,8423706802132,3942470355212,15422983070704,1625889380786,2977073689630,2911038273534),
'ARMv7': (9744762652972,9363084560380,4986396938104,1402608533080,7845317433440,14660726284368,10856135253016,9097960465448,13762176079688,2396927292560,4456937953472,4077539159464),
'ARMv8': (8919750364756, 9356368676660, 3757329928944, 1200100321484, 7250582939124,12229715680908,9976458458776,6250954278068,13431433283368,2177450043276,3990424119164,3625451990696),
'x86-64':(8040307629188,8733495095292,3567018301833,998734650367,6643187200833,10370565659370,9156256088675,4798161091073,12024400475495,2047824858499,3643490730307,3182591006165)
}

# total instructions -O3 (or micro-ops, or macro-ops)
total_insts_data = {
    'RV64G':            (2446903252366,3006654994137,1313303322578,276824124425,1946964385627,2929005977979,2872360411438,1365591667087,4841396527506,578572760390, 936919528518, 990256235560),
    'RV64GC macro-ops': (2373911481082,2441457750229,1294339550838,274916193763,1823132123900,2927888717150,2588246109084,1365357825233,4303734258211,569565919499, 848099712976, 988293691002),
    'ARMv7':            (2436190663243,2340771140095,1246599234526,350652133270,1961329358360,3665181571092,2714033813254,2274490116362,3440544019922,599231823140,1114234488368,1019384789866),
    'ARMv8':            (2229937591189,2339092169165,939332482236, 300025080371,1812645734781,3057428920227,2494114614694,1562738569517,3357858320842,544362510819, 997606029791, 906362997674),
    'ARMv8 micro-ops':  (2280667418788,2481789456379,941892402104, 310104773044,1845509210612,3213026192094,2498446001612,1580783037916,3495334680450,600492779754,1043421150868, 960530017021),
    'ia32':             (2170912961726,2372920217432, 997123972225,315737725906,1651569080869,2996165622128,2359380480175,2675016034413,3054004230248,661726492091,1055630710617, 951684494860),
    'x86-64':           (2091432249933,2260212572889, 963603237022,294173914876,1645784489833,2525716510935,2223233518226,1649060223079,2952759491576,553138169594, 949003395478, 863957172176),
    'x86-64 micro-ops': (2367182896653,2523738832163,1143066194842,305190626911,1825446671900,3700686618705,2376142609898,1454756704714,4348889582573,687664996934, 989392918261, 926067856035)
}



bmarks=["400.perlbench", "401.bzip2", "403.gcc", "429.mcf", "445.gobmk", "456.hmmer", "458.sjeng", "462.libquantum", "464.h264ref", "471.omnetpp", "473.astar", "483.xalancbmk"]

     
cmap = matplotlib.pyplot.get_cmap("viridis_r")
#cmap = matplotlib.pyplot.get_cmap("Accent")
#print dir(cmap)
#all_colors = cmap.from_list()

max_colors = 13
color_intensities = [float(x)/(max_colors-1) for x in range(max_colors)]
vircol = [matplotlib.cm.viridis(c) for c in color_intensities]
      
def getColor(idx):
#    n = cmap.N
#    i = (40*idx + 10*(idx/n) + 0) % n
#    print i
#    return colors[idx%13]
    return vircol[idx]

def geomean(nums):
    return (reduce(lambda x, y: x*y, nums))**(1.0/len(nums))

def plot_dynamic_bytes(plotter):
    plt.title("Total Dynamic Bytes", fontsize=9)

    # normalize data, then add geomean
    data = dynamic_bytes_data
    norm = {}
    for k in data:
        norm[k] = [float(n)/d for (n,d) in zip(data[k],data['x86-64'])]
        norm[k].append(geomean(norm[k]))

    # plot data
    num_points = len(norm['RV64G'])
    idx = np.arange(0,num_points)
    width = 1.0/(len(data.keys())+1)

    plt.gca().yaxis.grid(True)
    plt.gca().set_axisbelow(True)
    # love 0,6,11 for colors
    plotter.bar(idx+width*0, norm['x86-64'], width, color=getColor(2), label='x86-64', align='center')
    plotter.bar(idx+width*1, norm['ARMv7'],  width, color=getColor(6), label='ARMv7', align='center')
    plotter.bar(idx+width*2, norm['ARMv8'],  width, color=getColor(8), label='ARMv8', align='center')
    plotter.bar(idx+width*3, norm['RV64G'],  width, color=getColor(10), label='RV64G' , align='center')
    plotter.bar(idx+width*4, norm['RV64GC'], width, color=getColor(12), label='RV64GC', align='center')
     
    plt.xlim([0-width,num_points-1.25*width])
    locs,labels = plt.yticks()
    plotter.set_ylabel('dynamic instruction bytes\n(normalized to x86-64)')
    plotter.set_xlabel('benchmarks')
    plotter.xaxis.labelpad = 0 
    bmarks.append('geomean')
    plt.xticks(idx + width, bmarks, rotation='-30',size='small')
    plt.legend(fontsize=6, bbox_to_anchor=(1,1.1))
          

def plot_inst_counts(plotter):
    plt.title("Total Dynamic Instructions", fontsize=9)

    # normalize data, then add geomean
    data = total_insts_data
    norm = {}
    for k in data:
        norm[k] = [float(n)/d for (n,d) in zip(data[k],data['x86-64'])]
        norm[k].append(geomean(norm[k]))

    # plot data
    num_points = len(norm['RV64G'])
    idx = np.arange(0,num_points)
    print len(data.keys())-1
    width = 1.0/(len(data.keys())+1-1)

    plt.gca().yaxis.grid(True)
    plt.gca().set_axisbelow(True)
     
    plotter.bar(idx+width*0, norm['x86-64 micro-ops'],  width, color=getColor( 0), label='x86-64 micro-ops', align='center')
    plotter.bar(idx+width*1, norm['x86-64'],            width, color=getColor( 2), label='x86-64', align='center')
    plotter.bar(idx+width*2, norm['ia32'],              width, color=getColor( 4), label='ia32', align='center')
    plotter.bar(idx+width*3, norm['ARMv7'],             width, color=getColor( 6), label='ARMv7', align='center')
    plotter.bar(idx+width*4, norm['ARMv8'],             width, color=getColor( 8), label='ARMv8', align='center')
    plotter.bar(idx+width*5, norm['RV64G'],             width, color=getColor(10), label='RV64G' , align='center')
    plotter.bar(idx+width*6, norm['RV64GC macro-ops'],  width, color=getColor(12), label='RV64GC macro-ops', align='center')
     
    plt.xlim([0-width,num_points-1.05*width])
    locs,labels = plt.yticks()
    plotter.set_ylabel('dynamic instructions\n(normalized to x86-64)')
    plotter.set_xlabel('benchmarks')
    plotter.xaxis.labelpad = 0 
    bmarks.append('geomean')
    plt.xticks(idx + width, bmarks, rotation='-30',size='small')
    plt.legend(fontsize=6, bbox_to_anchor=(1,1.23))# for tech report
#    plt.legend(fontsize=6, bbox_to_anchor=(1,1.0)) #for ppt
         

def addTextLabel(plotter, x, value):
    plotter.text(x, value, "%4.2f" % (value), horizontalalignment='center',verticalalignment='bottom')

def plot_inst_counts_geomean(plotter):
    plt.title("Total Dynamic Instructions", fontsize=9)

    # normalize data, then add geomean
    data = total_insts_data
    norm = {}
    for k in data:
        norm[k] = [float(n)/d for (n,d) in zip(data[k],data['x86-64'])]
        # clear to only store the geomean
        norm[k] = [geomean(norm[k])]

    # plot data
    num_points = len(norm['RV64G'])
    assert (num_points == 1)
    idx = np.arange(0,num_points)
    print len(data.keys())
    width = 0.083
#    width = 1.0/(len(data.keys())+1)
    off = width + 0.05

    plt.gca().yaxis.grid(True)
    plt.gca().set_axisbelow(True)
    plotter.bar(idx+off*0, norm['x86-64 micro-ops'],  width, color=getColor( 0), label='x86-64 micro-ops', align='center')
    plotter.bar(idx+off*1, norm['x86-64'],            width, color=getColor( 2), label='x86-64', align='center')
    plotter.bar(idx+off*2, norm['ia32'],              width, color=getColor( 4), label='ia32', align='center')
    plotter.bar(idx+off*3, norm['ARMv7'],             width, color=getColor( 6), label='ARMv7', align='center')
    plotter.bar(idx+off*4, norm['ARMv8'],             width, color=getColor( 8), label='ARMv8', align='center')
    plotter.bar(idx+off*5, norm['ARMv8 micro-ops'],   width, color=getColor( 9), label='ARMv8 micro-ops', align='center')
    plotter.bar(idx+off*6, norm['RV64G'],             width, color=getColor(10),  label='RV64G' , align='center')
    plotter.bar(idx+off*7, norm['RV64GC macro-ops'],  width, color=getColor(12),  label='RV64GC macro-ops', align='center')
    
    print "--------"
    print norm['x86-64 micro-ops']

    addTextLabel(plotter, idx+off*0, norm['x86-64 micro-ops'][0])
    addTextLabel(plotter, idx+off*1, norm['x86-64'][0])
    addTextLabel(plotter, idx+off*2, norm['ia32'][0])
    addTextLabel(plotter, idx+off*3, norm['ARMv7'][0])
    addTextLabel(plotter, idx+off*4, norm['ARMv8'][0])
    addTextLabel(plotter, idx+off*5, norm['ARMv8 micro-ops'][0])
    addTextLabel(plotter, idx+off*6, norm['RV64G'][0])
    addTextLabel(plotter, idx+off*7, norm['RV64GC macro-ops'][0])
     
    plt.xlim([0-width,num_points+.125*width])
    plotter.set_ylabel('dynamic instructions\n(normalized to x86-64)')
    plotter.set_xlabel('Geometric Mean')
    plotter.get_xaxis().set_ticks([])
    plotter.xaxis.labelpad = 3 
    plt.legend(fontsize=6, bbox_to_anchor=(1.45,0.45))
          
     
def main():

    # Plotting
 
    font = {#'family' : 'normal',
            #'weight' : 'bold',
            'size'   : 8}
    matplotlib.rc('font', **font)
    cmap = matplotlib.pyplot.get_cmap("viridis")
    print "Cmap Number: ", cmap.N
  
    NUM_FIGS = 1
   
    fig = plt.figure(figsize=(7.2,2.5)) # dynamic
#    fig = plt.figure(figsize=(7.2,4.8)) #inst count for ppt
    p1 = fig.add_subplot(NUM_FIGS,1,1)
    fig.subplots_adjust(bottom=0.2, left=0.1, right=0.98)
    plot_dynamic_bytes(p1)
    gname = "./graphs/dynamicbytes.pdf"
    plt.savefig(gname)
    print ("Saving plot at : " + gname)
 
    scale = 1.0
#    fig = plt.figure(figsize=(scale*7.2,scale*4.8)) #inst count for ppt
    fig = plt.figure(figsize=(7.2,2.8)) #inst count for techreport
    plt.gcf().clear()
    p1 = fig.add_subplot(NUM_FIGS,1,1)
    fig.subplots_adjust(bottom=0.18, top=0.85, left=0.1, right=0.98)
    plot_inst_counts(p1)
    gname = "./graphs/instcounts.pdf"
    plt.savefig(gname)
    print ("Saving plot at : " + gname)
    
    plt.gcf().clear()
    fig = plt.figure(figsize=(3.5,2.5))
    fig.subplots_adjust(bottom=0.11, top=0.90, left=0.16, right=0.74)
    p1 = fig.add_subplot(NUM_FIGS,1,1)
    plot_inst_counts_geomean(p1)
    gname = "./graphs/instcounts_geomean.pdf"
    plt.savefig(gname)
    print ("Saving plot at : " + gname)
     
 

if __name__ == '__main__':
  main()

