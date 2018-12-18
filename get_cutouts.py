#!/usr/bin/env python3

import os
import sys
import numpy

import multiprocessing
from urllib.request import urlopen


def download_cutout(coord_queue, out_dir, format='jpg'):

    while (True):

        cmd = coord_queue.get()
        if (cmd is None):
            coord_queue.task_done()
            break

        ra,dec = cmd
        print(ra,dec)

# http://ps1images.stsci.edu/cgi-bin/fitscut.cgi?
# red=/rings.v3.skycell/2166/030/rings.v3.skycell.2166.030.stk.y.unconv.fits&
# blue=/rings.v3.skycell/2166/030/rings.v3.skycell.2166.030.stk.g.unconv.fits&
# green=/rings.v3.skycell/2166/030/rings.v3.skycell.2166.030.stk.i.unconv.fits&\
#                                                       x=49.950670&\
#                                                         y=41.511700&\
#                                                           size=240&\
#                                                                wcs=1&\
#                                                                    asinh=True&\
#                                                                          autoscale=99.750000


        # get list of files for these coords
        url = "http://ps1images.stsci.edu/cgi-bin/ps1filenames.py?ra=%f&dec=%f&filters=gri&type=stack" % (ra,dec)
        # print(url)
        file_query = urlopen(url)
        results = file_query.read()
        filter_dict = {'g': None, 'r': None, 'i': None}
        for line in results.splitlines()[1:]:
            items = line.decode('ascii').split()
            filtername = items[4]
            fn = items[7]
            filter_dict[filtername] = fn
            # print(filtername, fn)
        # print(results)


        # generate download url
        # print(filter_dict)
        url = 'http://ps1images.stsci.edu/cgi-bin/fitscut.cgi?ra=%f&dec=%f&format=jpeg&size=512&red=%s&green=%s&blue=%s&asinh=True' % (
            ra, dec, filter_dict['i'], filter_dict['r'], filter_dict['g'])

        # download the image
        # print(url)

        response = urlopen(url)
        if (response.getcode() != 200):
            return None
        cutout_data = response.read()

        output_fn = "cutout_%09.5f%+08.5f.jpg" % (ra, dec)
        with open(output_fn, "wb") as of:
            of.write(cutout_data)

        coord_queue.task_done()


if __name__ == "__main__":

    coord_fn = sys.argv[1]
    fov = float(sys.argv[2])


    coords = numpy.loadtxt(coord_fn)
    coord_queue = multiprocessing.JoinableQueue()

    for coord in coords:
        coord_queue.put((coord[0], coord[1]))
        # break
    print("all done queuing up coordinates")

    processes = []
    for i in range(5):
        # add termination token
        coord_queue.put((None))

        # start parallel worker process
        p = multiprocessing.Process(
            target=download_cutout,
            kwargs=dict(
                coord_queue=coord_queue,
                out_dir=".",
                format='jpg',
            )
        )
        p.daemon = True
        p.start()
        processes.append(p)

    # now wait for all work to be done
    coord_queue.join()
