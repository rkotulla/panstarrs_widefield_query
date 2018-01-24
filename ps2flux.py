#!/usr/bin/env python

import os
import sys
import pyfits
import numpy


if __name__ == "__main__":

    postfix = sys.argv[1]
    filelist = sys.argv[2:]

    # in_fn = sys.argv[1]
    # out_fn = sys.argv[2]

    for in_fn in filelist:
        out_fn = in_fn[:-5]+".linear.fits"
        if (os.path.isfile(out_fn)):
            print "skipping %s, %s already exists" % (in_fn, out_fn)
            continue

        print "%s --> %s" % (in_fn, out_fn)


        hdulist = pyfits.open(in_fn)
        data = hdulist[0].data

        hdr = hdulist[0].header
        #bzero = hdr['BZERO']
        #bscale = hdr['BSCALE']
        bsoften = hdr['BSOFTEN']
        boffset = hdr['BOFFSET']

        a = 2.5 * numpy.log10(numpy.e)
        # print a

        true = data #* bscale + bzero
        linear = 2 * bsoften * numpy.sinh(true/a)

        hdulist[0].data = linear.astype(numpy.float32)
        hdulist.writeto(out_fn, clobber=True)


