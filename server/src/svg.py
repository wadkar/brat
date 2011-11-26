#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# vim:set ft=python ts=4 sw=4 sts=4 autoindent:

'''
SVG saving and storage functionality.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Author:     Goran Topic         <goran is s u-tokyo ac jp>
Version:    2011-04-22
'''

# TODO: Can we verify somehow that what we are getting is actually an svg?
# TODO: Limits to size? Or inherent from HTTP?

from __future__ import with_statement

from os.path import join as path_join
from os.path import isfile, exists
from os import makedirs, mkdir

from common import ProtocolError, NoPrintJSONError
from config import BASE_DIR, WORK_DIR
from document import real_directory
from message import Messager
from session import get_session

### Constants
SVG_DIR = path_join(WORK_DIR, 'svg')
CSS_PATH = path_join(BASE_DIR, 'style.css')
FONT_DIR = path_join(BASE_DIR, 'static', 'fonts')
SVG_FONTS = (
        path_join(FONT_DIR, 'Liberation_Sans-Regular.svg'),
        path_join(FONT_DIR, 'PT_Sans-Caption-Web-Regular.svg'),
        )
SVG_SUFFIX='svg'
# Maintain a mirror of the data directory where we keep the latest stored svg
#   for each document. Incurs some disk write overhead.
SVG_STORE_DIR = path_join(WORK_DIR, 'svg_store')
SVG_STORE = False
###


class UnknownSVGVersionError(ProtocolError):
    def __init__(self, unknown_version):
        self.unknown_version = unknown_version

    def __str__(self):
        return 'Version "%s" is not a valid version' % self.unknown_version

    def json(self, json_dic):
        json_dic['exception'] = 'unknownSVGVersion'
        return json_dic


class NoSVGError(ProtocolError):
    def __init__(self, version):
        self.version = version

    def __str__(self):
        return 'SVG with version "%s" does not exist' % (self.version, )

    def json(self, json_dic):
        json_dic['exception'] = 'noSVG'
        return json_dic


class CorruptSVGError(ProtocolError):
    def __init__(self):
        pass

    def __str__(self):
        return 'Corrupt SVG'

    def json(self, json_dic):
        json_dic['exception'] = 'corruptSVG'
        return json_dic


def _save_svg(collection, document, svg):
    svg_path = _stored_path()+'.'+SVG_SUFFIX

    with open(svg_path, 'w') as svg_file:
        svg_hdr = ('<?xml version="1.0" standalone="no"?>'
                '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
                '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
        defs = svg.find('</defs>')

        with open(CSS_PATH, 'r') as css_file:
            css = css_file.read()

        if defs != -1:
            css = '<style type="text/css"><![CDATA[' + css + ']]></style>'
            font_data = []
            for font_path in SVG_FONTS:
                with open(font_path, 'r') as font_file:
                    font_data.append(font_file.read().strip())
            fonts = '\n'.join(font_data)
            svg = (svg_hdr + '\n' + svg[:defs] + '\n' + fonts + '\n' + css
                    + '\n' + svg[defs:])
            svg_file.write(svg)

            # Create a copy in the svg store?
            if SVG_STORE:
                real_dir = real_directory(collection, rel_to=SVG_STORE_DIR)
                if not exists(real_dir):
                    makedirs(real_dir)
                svg_store_path = path_join(real_dir, document + '.svg')
                with open(svg_store_path, 'w') as svg_store_file:
                    svg_store_file.write(svg)

        else:
            # TODO: @amadanmath: When does this actually happen?
            raise CorruptSVGError


def _stored_path():
    # Create the SVG_DIR if necessary
    if not exists(SVG_DIR):
        mkdir(SVG_DIR)

    return path_join(SVG_DIR, get_session().sid)

def store_svg(collection, document, svg):
    stored = []

    _save_svg(collection, document, svg)
    stored.append({'name': 'svg', 'suffix': SVG_SUFFIX})

    return { 'stored' : stored }

def retrieve_stored(document, suffix):
    svg_path = _stored_path()+'.'+suffix

    if not isfile(svg_path):
        raise NoSVGError(version)

    # Bail out with a hack since we violated the protocol
    hdrs = [('Content-Type', 'image/svg+xml'),
            ('Content-Disposition', 'inline; filename=' + document + '.svg')]
    with open(svg_path, 'r') as svg_file:
        data = svg_file.read()
    raise NoPrintJSONError(hdrs, data)
