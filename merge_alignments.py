# -*- coding: utf-8 -*-

import argparse

from lxml import etree


def merge(files_in, file_out):
    root = etree.Element('cesAlign', attrib={'version': '1.0'})

    for file_in in files_in:
        parser = etree.XMLParser(remove_blank_text=True)
        in_tree = etree.parse(file_in, parser)

        for linkGrp in in_tree.xpath('//linkGrp'):
            root.set('fromDoc', linkGrp.get('fromDoc').split('/')[0])
            root.set('toDoc', linkGrp.get('toDoc').split('/')[0])
            root.append(linkGrp)

    tree = etree.ElementTree(root)
    tree.docinfo.public_id = '-//CES//DTD XML cesAlign//EN'
    tree.docinfo.system_url = 'dtd/xcesAlign.dtd'
    tree.write(file_out, pretty_print=True, xml_declaration=True, encoding='utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file_in', type=str, nargs='+', help='Input files')
    parser.add_argument('file_out', type=str, help='Output file')
    args = parser.parse_args()

    merge(args.file_in, args.file_out)
