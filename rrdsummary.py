#!/usr/bin/python -tt
__author__ = 'Ilia Shakitko'

import xml.etree.ElementTree as ET
import argparse
import PIParser
import subprocess
import sys

# Parsing arguments
p = argparse.ArgumentParser(description="Summarise given rrd reports and saves result into a file")
p.add_argument('files', metavar='FILENAME', type=str, nargs='+', help='RRD xml files list (whitespace separated;' +
                                                                      ' must be located in the same folder)')
p.add_argument('--summary', '-s', type=str, default='summary.xml', help='Output file name (default "summary.xml")')
args = p.parse_args()

def process_dom_rows(rows, rra_index, strategy, dom_xml_filedata):
    one_point_offset = int(len(rows)/100);
    if one_point_offset == 0:
        one_point_offset = 1

    print('Processing rows of rra#%s with strategy: %s\n[' % (rra_index, strategy)),
    for row_index, row in enumerate(rows):
        # there are 3 items in each row
        filedata_items = {0: [], 1: [], 2: []}

        # go thru file list and pick up 3 values from respective row
        for file in args.files:
            tree = dom_xml_filedata[file]
            rra = tree.findall('rra')
            subfile_rows = rra[rra_index].find('database').findall('row')

            # append values to 3 lists
            filedata_items[0].append(float(subfile_rows[row_index][0].text))
            filedata_items[1].append(float(subfile_rows[row_index][1].text))
            filedata_items[2].append(float(subfile_rows[row_index][2].text))

        # replace summary values for 3 items of the row with aggregated value
        row[0].text = '%.10e' % sum(filedata_items[0])
        row[1].text = '%.10e' % sum(filedata_items[1])
        row[2].text = '%.10e' % sum(filedata_items[2])

        # print process if applicable
        if row_index%one_point_offset == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

    print(']\n')


def main():
    dom_xml_filedata = {}
    files = args.files
    summary_file_name = args.summary

    # exit if no files provided
    if len(args.files) == 0:
        print('No files specified')
        exit(1)

    ## read all files
    print('Reading and parsing files ...\n')
    for filename in files:
        print('parsing file %s' % filename)
        dom_xml_filedata[filename] = ET.parse(filename)
    print('\nFiles has been parsed. Begin aggregation...\n')

    #copy first file as summary
    subprocess.call(['cp', files[0], summary_file_name])

    # read XML tree with PIParser (for persist comments)
    tree = ET.parse(summary_file_name, PIParser.PIParser())
    root = tree.getroot()

    # iterate over each "rra" node
    for rra_index, rra in enumerate(root.findall('rra')):
        # MAX, MIN or AVERAGE
        strategy = rra.find('cf')
        rows = rra.find('database').findall('row')

        #iterate over each "row" node
        process_dom_rows(rows=rows, rra_index=rra_index, strategy=strategy.text.lower(), dom_xml_filedata=dom_xml_filedata)
        print('%s rows of rra node#%s has been processed\n' % (len(rows), rra_index))
    print('-----------------------------------------------------\n')
    print('All rra records has been proceessed\n')

    # save summary tree to the file
    print('Saving data to file')
    file_handle = open(summary_file_name, "wb")
    file_handle.write(
        '<?xml version="1.0" encoding="utf-8"?>\n' +
        '<!DOCTYPE rrd SYSTEM "http://oss.oetiker.ch/rrdtool/rrdtool.dtd">\n' +
        '<!-- Round Robin Database Dump -->\n' +
        ET.tostring(tree.getroot())
    )
    file_handle.close()
    print('Data saved')

if __name__ == '__main__':
    main()