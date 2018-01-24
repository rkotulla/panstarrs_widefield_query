#!/usr/bin/env python

import os
import sys
import pyfits
import numpy
import urllib2
import argparse

def parse_commandline():

    parser = argparse.ArgumentParser()

    parser.add_argument("target_ra", #nargs=1,
                        type=float,
            help="Target Right Ascension [degrees]")

    parser.add_argument("target_dec", #nargs=1,
                        type=float,
            help="Target Declination [degrees]")

    parser.add_argument("radius", #nargs=1,
                        type=float,
            help="Radius [degrees]")

    parser.add_argument(
        "--wget",
        default='wget.list',
        help="output filename for wget script")

    args = parser.parse_args()
    return args


def query(ra,dec):

    url = "http://ps1images.stsci.edu/cgi-bin/ps1filenames.py?ra=%.3f&dec=%.3f&filters=griz&type=stack,stack.wt" % (ra, dec)

    response = urllib2.urlopen(url)

    if (response.getcode() != 200):
        return None

    ps_string = response.read()

    ps_data = []
    for line in ps_string.splitlines()[1:]:
        # print line
        items = line.split()
        ps_data.append([int(items[0]), #projcell
                        int(items[1]), #subcell
                        float(items[2]), #ra
                        float(items[3]), #dec
                        items[4], #filter
#                       items[5], #mjd
                        items[6], #type
                        items[7], #filename
                        items[8], #shortname
                        ])

    return ps_data

if __name__ == "__main__":

    args = parse_commandline()

    target_ra = args.target_ra
    target_dec = args.target_dec
    radius = args.radius

    wget_filename = args.wget


    # now create a box spanning the ra/dec range
    dec_list = numpy.arange(start=target_dec-radius,
                            stop=target_dec+radius+0.2,
                            step=0.2)
    print dec_list

    cos_dec = numpy.cos(numpy.radians(dec_list))
    min_cos_dec = numpy.min(cos_dec)
    max_cos_dec = numpy.min(cos_dec)

    ra_step = 0.2/max_cos_dec
    ra_list = numpy.arange(start=target_ra-radius/min_cos_dec,
                           stop=target_ra+radius/min_cos_dec+ra_step,
                           step=ra_step)
    print ra_list


    fields = []
    for ra in ra_list:
        for dec in dec_list:
            print ra, dec
            new_fields = query(ra, dec)
            fields.extend(new_fields)

    # print fields

    fields = numpy.array(fields)

    filenames = fields[:, 6]
    # print filenames
    print "Found %d (non-unique) files in total" % (filenames.shape[0])

    unique_files = set(filenames)
    print "reduced download-queue to %d unique files" % (len(unique_files))

    # now re-assemble the full data for each of the unique files
    final_answer_idx = []
    for uf in unique_files:
        idx = numpy.where(fields[:,6]==uf)
        # print idx, idx[0][0]
        final_answer_idx.append(idx[0][0])

    print final_answer_idx
    final_answer = fields[final_answer_idx]

    print final_answer.shape

    wget = open(wget_filename, "w")
    for fa in final_answer:
        print >>wget, "wget -O %s.fz http://ps1images.stsci.edu/%s" % (
            fa[7], fa[6]
        )


