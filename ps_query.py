#!/usr/bin/env python3

import os
import sys
import astropy.io.fits as pyfits
import numpy
import urllib.request
import argparse
import itertools

import astroquery
from astroquery.simbad import Simbad
import ephem

def parse_commandline():

    parser = argparse.ArgumentParser()

    # parser.add_argument("target_ra", #nargs=1,
    #                     type=float,
    #         help="Target Right Ascension [degrees]")
    #
    # parser.add_argument("target_dec", #nargs=1,
    #                     type=float,
    #         help="Target Declination [degrees]")

    parser.add_argument(
        "-r", "--radius", #nargs=1,
        type=float, default=0.2,  help="Radius [degrees]"
    )

    parser.add_argument(
        "--wget",
        default='wget.list',
        help="output filename for wget script"
    )

    parser.add_argument("input_targets", nargs="+",
                         help="list of input coordinates and/or object names")

    args = parser.parse_args()
    return args



def resolve_name_to_radec(objname):

    bad_return = None, None

    print("querying Simbad")
    try:
        results = Simbad.query_object(objname)
    except:
        return bad_return

    if (results is None):
        return bad_return

    # print(results[0][1])
    # print(results[0][2])
    #
    # print type(results[0][1])

    _ra  = results[0][1].replace(" ", ":")
    _dec = results[0][2].replace(" ", ":")

    e = ephem.Equatorial(str(_ra), str(_dec))
    # print(e)
    # print(e.ra, e.dec)

    return numpy.degrees(e.ra), numpy.degrees(e.dec)



def query(ra,dec, dump=False):

    url = "http://ps1images.stsci.edu/cgi-bin/ps1filenames.py?ra=%.3f&dec=%.3f&filters=griz&type=stack,stack.wt" % (ra, dec)

    response = urllib.request.urlopen(url)

    if (response.getcode() != 200):
        return None

    ps_string = response.read().decode("utf-8")

    if (dump):
        dumpfile = "dump__%010.6f%+011.6f" % (ra, dec)
        with open(dumpfile, "w") as df:
            df.write(str(ps_string))

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
                        str(items[7]), #filename
                        str(items[8]), #shortname
                        ])

    return ps_data


def create_panstarrs_filelist(target_ra, target_dec, radius, wget_filename):

    # now create a box spanning the ra/dec range
    dec_list = numpy.arange(start=target_dec-radius,
                            stop=target_dec+radius+0.2,
                            step=0.2)
    # print(dec_list)

    cos_dec = numpy.cos(numpy.radians(dec_list))
    min_cos_dec = numpy.min(cos_dec)
    max_cos_dec = numpy.min(cos_dec)

    ra_step = 0.2/max_cos_dec
    ra_list = numpy.arange(start=target_ra-radius/min_cos_dec,
                           stop=target_ra+radius/min_cos_dec+ra_step,
                           step=ra_step)
    # print(ra_list)


    fields = []
    ra_dec_list = list(itertools.product(ra_list, dec_list))
    for i, (ra,dec) in enumerate(ra_dec_list):
        sys.stdout.write("\rQuerying field %3d of %3d (%9.5f, %+9.5f)" % (
            i+1, len(ra_dec_list), ra, dec
        ))
        sys.stdout.flush()

        new_fields = query(ra, dec)
        fields.extend(new_fields)
    print(" done!")
    # print fields

    fields = numpy.array(fields)

    filenames = fields[:, 6]
    # print filenames
    print("Found %d (non-unique) files in total" % (filenames.shape[0]))

    unique_files = set(filenames)
    print("reduced download-queue to %d unique files" % (len(unique_files)))

    # now re-assemble the full data for each of the unique files
    final_answer_idx = []
    for uf in unique_files:
        idx = numpy.where(fields[:,6]==uf)
        # print idx, idx[0][0]
        final_answer_idx.append(idx[0][0])

    # print(final_answer_idx)
    final_answer = fields[final_answer_idx]

    # print(final_answer.shape)

    with open(wget_filename, "w") as wget:
        for fa in final_answer:
            print("wget -O %s.fz https://ps1images.stsci.edu/%s" % (str(fa[7]), str(fa[6])),
                  file=wget)



if __name__ == "__main__":

    args = parse_commandline()


    for target in args.input_targets:

        # check if input is in format ra+dec or ra-dec
        if (len(target.split("+")) == 2):
            items = target.split("+")
            ra = float(items[0])
            dec = float(items[1])
            print("Identifying input as coordinates: %s ==> %.5f %+.5f" % (target, ra, dec))
        elif (len(target.split("-")) == 2):
            items = target.split("-")
            ra = float(items[0])
            dec = float(items[1])
            print("Identifying input as coordinates: %s ==> %.5f %+.5f" % (target, ra, dec))
        else:
            # interpret this as a object name
            ra, dec = 0,0
            ra, dec = resolve_name_to_radec(target)
            if (ra is None or dec is None):
                print("Unable to resolve %s" % (target))
                continue
            else:
                print("Resolving target name %s ==> %.5f %+.5f" % (target, ra, dec))

        # target_ra = args.target_ra
        # target_dec = args.target_dec
        # radius = args.radius
        wget_filename = "%s_%s_r=%.1f" % (args.wget, target, args.radius)

        create_panstarrs_filelist(
            target_ra=ra, target_dec=dec,
            radius=args.radius,
            wget_filename=wget_filename
        )




