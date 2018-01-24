# panstarrs_widefield_query

this tool allows to download panstarrs data over a wider field of view than is 
possible using only the panstarrs image cutout service.

It takes a center ra/dec and a radius from the user and then queries panstarrs
for the indivual patches that cover the specified area. primary program output 
then is a wget script to download the data. After some post-processing using the 
ps2flux.py tool to convert image data into actual fluxes the final files can then 
be combined using standard tools such as swarp.
