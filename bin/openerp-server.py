#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
OpenERP - Server
OpenERP is an ERP+CRM program for small and medium businesses.

The whole source code is distributed under the terms of the
GNU Public Licence.

(c) 2003-TODAY, Fabien Pinckaers - Tiny sprl
"""

#----------------------------------------------------------
# python imports
#----------------------------------------------------------
import logging
import os
import signal
import sys
import threading
import traceback

import release
__author__ = release.author
__version__ = release.version

#----------------------------------------------------------
# get logger
#----------------------------------------------------------
import netsvc
logger = netsvc.Logger()

#-----------------------------------------------------------------------
# import the tools module so that the commandline parameters are parsed
#-----------------------------------------------------------------------
import tools

logger.notifyChannel("server", netsvc.LOG_INFO, "version - %s" % release.version )
for name, value in [('addons_path', tools.config['addons_path']),
                    ('database hostname', tools.config['db_host'] or 'localhost'),
                    ('database port', tools.config['db_port'] or '5432'),
                    ('database user', tools.config['db_user'])]:
    logger.notifyChannel("server", netsvc.LOG_INFO, "%s - %s" % ( name, value ))

import time

if sys.platform == 'win32':
    import mx.DateTime
    mx.DateTime.strptime = lambda x, y: mx.DateTime.mktime(time.strptime(x, y))

#----------------------------------------------------------
# init net service
#----------------------------------------------------------
logger.notifyChannel("objects", netsvc.LOG_INFO, 'initialising distributed objects services')

#---------------------------------------------------------------
# connect to the database and initialize it with base if needed
#---------------------------------------------------------------
import pooler

#----------------------------------------------------------
# import basic modules
#----------------------------------------------------------
import osv
import workflow
import report
import service

#----------------------------------------------------------
# import addons
#----------------------------------------------------------

import addons

#----------------------------------------------------------
# Load and update databases if requested
#----------------------------------------------------------

if tools.config['db_name']:
    for db in tools.config['db_name'].split(','):
        pooler.get_db_and_pool(db, update_module=tools.config['init'] or tools.config['update'])

#----------------------------------------------------------
# translation stuff
#----------------------------------------------------------
if tools.config["translate_out"]:
    import csv

    if tools.config["language"]:
        msg = "language %s" % (tools.config["language"],)
    else:
        msg = "new language"
    logger.notifyChannel("init", netsvc.LOG_INFO, 
                         'writing translation file for %s to %s' % (msg, 
                                                                    tools.config["translate_out"]))

    fileformat = os.path.splitext(tools.config["translate_out"])[-1][1:].lower()
    buf = file(tools.config["translate_out"], "w")
    tools.trans_export(tools.config["language"], tools.config["translate_modules"], buf, fileformat)
    buf.close()

    logger.notifyChannel("init", netsvc.LOG_INFO, 'translation file written successfully')
    sys.exit(0)

if tools.config["translate_in"]:
    tools.trans_load(tools.config["db_name"], 
                     tools.config["translate_in"], 
                     tools.config["language"])
    sys.exit(0)

#----------------------------------------------------------------------------------
# if we don't want the server to continue to run after initialization, we quit here
#----------------------------------------------------------------------------------
if tools.config["stop_after_init"]:
    sys.exit(0)


#----------------------------------------------------------
# Register signal handlers
#----------------------------------------------------------
LST_SIGNALS = ['SIGINT', 'SIGTERM']

SIGNALS = dict(
    [(getattr(signal, sign), sign) for sign in LST_SIGNALS]
)

def handler(signum, frame):
    if tools.config['netrpc']:
        tinySocket.stop()
    if tools.config['xmlrpc']:
        httpd.stop()
    netsvc.Agent.quit()
    if tools.config['pidfile']:
        os.unlink(tools.config['pidfile'])
    logger.notifyChannel('shutdown', netsvc.LOG_INFO, "Shutdown Server! - %s" % ( SIGNALS[signum], ))
    logger.shutdown()
    sys.exit(0)

def dumpstacks(signum, frame):
    # code from http://stackoverflow.com/questions/132058/getting-stack-trace-from-a-running-python-application#answer-2569696
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name[threadId], threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))

    logger.notifyChannel("dumpstacks", netsvc.LOG_INFO, "\n".join(code))

for signum in SIGNALS:
    signal.signal(signum, handler)

if os.name == 'posix' and sys.version_info >= (2,5):
    signal.signal(signal.SIGQUIT, dumpstacks)

#----------------------------------------------------------
# Launch Server
#----------------------------------------------------------
if tools.config['xmlrpc']:
    port = int(tools.config['port'])
    interface = tools.config["interface"]
    secure = tools.config["secure"]

    httpd = netsvc.HttpDaemon(interface, port, secure)

    xml_gw = netsvc.xmlrpc.RpcGateway('web-services')
    httpd.attach("/xmlrpc", xml_gw)
    logger.notifyChannel("web-services", netsvc.LOG_INFO, 
                         "starting XML-RPC%s services, port %s" % 
                         ((tools.config['secure'] and ' Secure' or ''), port))

if tools.config['netrpc']:
    netport = int(tools.config['netport'])
    netinterface = tools.config["netinterface"]
    tinySocket = netsvc.TinySocketServerThread(netinterface, netport, False)
    logger.notifyChannel("web-services", netsvc.LOG_INFO, 
                         "starting NET-RPC service, port %d" % (netport,))

if tools.config['pidfile']:
    fd = open(tools.config['pidfile'], 'w')
    pidtext = "%d" % (os.getpid())
    fd.write(pidtext)
    fd.close()

logger.notifyChannel("web-services", netsvc.LOG_INFO, 
                     'the server is running, waiting for connections...')

if tools.config['netrpc']:
    tinySocket.start()
if tools.config['xmlrpc']:
    httpd.start()

while True:
    time.sleep(1)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

