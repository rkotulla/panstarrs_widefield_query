#!/usr/bin/env python3

import os
import sys
import numpy

import multiprocessing
from urllib.request import urlopen

# import PIL
# import PIL.Image
# import PIL.ImageDraw
from PIL import Image, ImageDraw, ImageFont

def download_cutout(coord_queue, out_dir, format='jpg'):

    while (True):

        cmd = coord_queue.get()
        if (cmd is None):
            coord_queue.task_done()
            break

        ra,dec,label = cmd
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

        final_fn = "cutout_%s__%09.5f%+08.5f.jpg" % (label.replace(" ", "_"), ra, dec)
        output_fn = "rawcutout_%s__%09.5f%+08.5f.jpg" % (label.replace(" ", "_"), ra, dec)
        with open(output_fn, "wb") as of:
            of.write(cutout_data)

        # now open the raw version of the file and add the label etc
        img = Image.open(output_fn)
        font = ImageFont.truetype("/usr/share/fonts/truetype/DroidSans.ttf", 24)
            #"arial.pil")
        draw = ImageDraw.Draw(img)
        pad = 3
        draw.text(xy=(pad,pad), text=label, font=font)

        radec_text = "%.5f%+.5f" % (ra,dec)
        dim = font.getsize(radec_text)
        # print(dim)
        imgsize = img.getbbox()
        if (imgsize is not None):
            x0,y0,x1,y1 = imgsize
        else:
            x0,y0,x1,y1 = 0,0,0,0
        # print(imgsize)
        dimx,dimy = dim
        draw.text(xy=(x1-dimx-pad, y1-dimy-pad), text=radec_text, font=font)

        img.save(final_fn)

        coord_queue.task_done()


if __name__ == "__main__":

    coord_fn = sys.argv[1]
    fov = float(sys.argv[2])


    coord_queue = multiprocessing.JoinableQueue()
    with open(coord_fn, "r") as cf:
        cflines = cf.readlines()
    for line in cflines:
        if line.startswith("#"):
            continue
        items = line.split()
        ra = float(items[0])
        dec = float(items[1])
        try:
            label = " ".join(items[2:])
        except:
            label = ""
        #
        # coords = numpy.loadtxt(coord_fn)
        # for coord in coords:
        print(label)
        coord_queue.put((ra, dec, label))

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
