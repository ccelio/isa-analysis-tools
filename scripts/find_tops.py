#!/usr/bin/env python
# Copyright (c) 2016, The Regents of the University of California (Regents).
# All Rights Reserved. See LICENSE for license details.
import optparse

def main():
  parser = optparse.OptionParser()
  parser.add_option('-f', '--file', dest='filename',
                    help='input histogram file')
  parser.add_option('-n', '--lines', dest='lines',
                    help='number of lines to print', default=20)
  (options, args) = parser.parse_args()
  if not options.filename:
    parser.error('Please give an input filename with -f')
  num_to_print = int(options.lines)
  f = open(options.filename)
  lines = map(lambda l: l.split(), f.readlines()[1:-4])
  freq_pc_pairs = map(lambda l: (int(l[1]), l[0]), lines)
  total_insts = sum(map(lambda p: p[0], freq_pc_pairs))
  freq_pc_pairs.sort(reverse=True)
  cdf_sum = 0.
  for freq, pc in freq_pc_pairs[:num_to_print]:
    percent = 100.*freq/total_insts
    cdf_sum += percent
    print '%8s %12u %8.3f%% %8.3f%%' % (pc, freq, percent, cdf_sum)
  print 'Total:%15u' % total_insts

if __name__ == '__main__':
  main()
