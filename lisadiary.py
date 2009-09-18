#!/usr/bin/env python
"""
Attempt to crawl the mercurial graph of the repository in the current
directory, to find out which files were most recently modified and which
files were most recently created. My mercurial-fu is not very good,
you have been warned.

ISSUES:
 * I don't know why, but sometimes I get the following exception when
 I do ctx.filectx(f):
    mercurial.error.LookupError: theano/sandbox/back_conv.py@8f941179a992: not found in manifest
 * I don't really know what the mercurial date format is, so my
 assumptions about the API might be incorrect.
 * I walk the entire repository graph. This might be slow.
"""

from common.mydict import sort as dictsort

import mercurial.error
from mercurial import hg,ui
#uio = ui.ui(debug=True,verbose=True)
uio = ui.ui()
r = hg.repository(ui=uio, path='.')

import logging
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)
logging.basicConfig(level=logging.DEBUG,)

filelastchanged = {}

# Walk every commit
ctxdone = {}
ctxtodo = [r[id] for id in r.heads()]
while len(ctxtodo) > 0:
    ctx = ctxtodo.pop()
    if ctx in ctxdone: continue
    logging.debug("Working on ctx %s" % `ctx`)

    # Look at every file in this commit
    for f in ctx.files():
        logging.debug("Looking at file %s" % f)
        try:
            fctx = ctx.filectx(f)
            assert fctx.path() == f
            if f not in filelastchanged: filelastchanged[f] = fctx.date()[0]

            # ISSUE: I'm not sure if it's correct to grab field 0. I don't know what field 1 does.
            if filelastchanged[f] < fctx.date()[0]:
                logging.debug("Updating last changed date of file %s from %f to %f" % (f, filelastchanged[f], fctx.date()[0]))
                filelastchanged[f] = fctx.date()[0]
        except mercurial.error.LookupError:
            # ISSUE: I have no idea why this exception occurs.
            logging.error("mercurial.error.LookupError on file %s at revision %s" % (ctx, f))

    ctxdone[ctx] = True
    for newctx in ctx.parents():
        if newctx in ctxdone: continue
        ctxtodo.append(newctx)

#for f in filelastchanged:
#    print f, filelastchanged[f]
print dictsort(filelastchanged)
