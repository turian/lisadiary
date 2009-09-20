#!/usr/bin/env python
"""
For each file in the repository, figure out where it was most
recently modified and when it was created. We do this by crawling
the entire mercurial graph of the repository in the current directory.
My mercurial-fu is not very good, you have been warned.

ISSUES:
 * I don't know why, but sometimes I get the following exception when
 I do ctx.filectx(f):
    mercurial.error.LookupError: theano/sandbox/back_conv.py@8f941179a992: not found in manifest
 * I don't really know what the mercurial date format is, so my
 assumptions about the API might be incorrect. The second value is the
 tz offset, but I don't use it.
 * I walk the entire repository graph. This might be slow.
 * I assume a file was created when a file context has no parents. I am
 not sure if this is correct.
 * If a file is created (as per the above definition) twice, I assume the
 earlier date as the file creation date. I am not sure if this is correct.
 * I don't think I am not able to determine when files were renamed.

"""

from common.mydict import sort as dictsort

import mercurial.error
from mercurial import hg,ui

import datetime

import logging
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)
logging.basicConfig(level=logging.DEBUG,)

def mercurial_time_to_datetime(t, tz):
    return datetime.datetime(1970,1,1).fromtimestamp(t)

def repository_file_revisions(path):
    """
    Given a path to a repository, return dicts:
        filelastchanged, filecreated
    """
    filelastchanged = {}
    filecreated = {}
    
    #uio = ui.ui(debug=True,verbose=True)
    uio = ui.ui()
    r = hg.repository(ui=uio, path=path)
    
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
                time = mercurial_time_to_datetime(fctx.date()[0], fctx.date()[1])
                if f not in filelastchanged: filelastchanged[f] = time
    
                # ISSUE: I'm not sure if it's correct to grab field 0. I don't know what field 1 does.
                if filelastchanged[f] < time:
                    logging.debug("Updating last changed date of file %s from %s to %s" % (f, filelastchanged[f], time))
                    filelastchanged[f] = time
    
                # Check if this file has no parents. If so, we assume that
                # this is when the file was created.
                # ISSUE: I am not sure if this is correct.
                if len(fctx.parents()) == 0:
                    logging.debug("File %s was created %s" % (f, time))
                    if f in filecreated:
                        logging.warning("File %s seems to have been created twice: %s and %s" % (f, time, filecreated[f]))
                        # If this file seems to have been created twice, pick the earlier date.
                        if filecreated[f] > time:
                            filecreated[f] = time
                    else:
                        filecreated[f] = time
                
            except mercurial.error.LookupError:
                # ISSUE: I have no idea why this exception occurs.
                logging.error("mercurial.error.LookupError on file %s at revision %s" % (ctx, f))
    
        ctxdone[ctx] = True
        for newctx in ctx.parents():
            if newctx in ctxdone: continue
            ctxtodo.append(newctx)
    
#    for f in filelastchanged:
#        print f, filelastchanged[f]
#    #    print datetime.datetime(1970,1,1).fromtimestamp(filelastchanged[f])
#    #print dictsort(filelastchanged)
#    print dictsort(filecreated)

    return filelastchanged, filecreated
