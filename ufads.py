#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

import sys
import os
from pathlib import Path
import argparse

import ufContentProvider

### Change this to something sensible
params = {
    'durShort':5,
    'durDefault':10,
    'durLong':20,
    'fadeTime':2,
    'fullscreen':False,
    'gui':False,
    'screen':None,
    'target':1,
    'paused':False,
    'splash':False,
    'offline':False,
    'splashImg':os.path.join(os.getcwd(),"unionfilms_white_201415.png"),
    'cacheDir':'/tmp',
    'title':'UnionFilms ScreenAds Display Client',
    'shortTitle':'ufScreenAds',
    'apiEndpoint':'https://unionfilms.org/screenads/',#'http://screenads.max.git.susu.org/screenads/'
}

def gui():
    from pyqtGui import entry, Gui
    entry()

if __name__ == '__main__':
    ### Args
    parser = argparse.ArgumentParser(description=params['title'])

    ufContentProvider.contentProviderArgParseSetup(parser)

    parser.add_argument('-s', '--screen', dest='screen', type=int, help='Specify a screen')
    parser.add_argument('-d', '--debug', action='store_true', help='Debugging messages')

    if params['gui']:
        parser.add_argument('--no-gui', dest='gui', action='store_const', const=False, default=True, help='Don\'t display a GUI')
    else:
        parser.add_argument('-g', '--gui', action='store_true', help='Display a GUI')
    if params['fullscreen']:
        parser.add_argument('--no-full', dest='fullscreen', action='store_const', const=False, default=True, help='No fullscreen')
    else:
        parser.add_argument('-f', '--full', dest='fullscreen', action='store_true', help='Fullscreen')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    params['cacheDir'] = os.path.join(str(Path.home()), params['shortTitle'])
    if not os.path.exists(params['cacheDir']):
        os.makedirs(params['cacheDir'])

    ### Changes to defaults
    params['fullscreen'] = args.fullscreen
    params['gui'] = args.gui

    ufContentProvider.contentProviderArgParseParse(args, params)

    ### pyglet
    from pyglet import canvas
    screens = canvas.get_display().get_screens()

    if len(screens) > 1:
        logger.debug('We have %d screens', len(screens))
        for i, screen in enumerate(screens):
            logger.debug('Screen %d | res = %d x %d | pos = %d , %d', i, screen.width, screen.height, screen.x, screen.y)

        if args.screen != None and args.screen >= 0 and len(screens) >= args.screen:
            logger.info('Using screen %d' %(args.screen))
            params['screen'] = args.screen
        elif args.screen == None and params['fullscreen']:
            print('Fullscreen mode requested but no screen specified (and there\'s more than one screen). Please specify a screen:')
            for i, screen in enumerate(screens):
                print('   Screen', i, '| res =', screen.width, 'x', screen.height, '| pos =', screen.x, ',', screen.y)
            sys.exit(1)
    else:
        logger.debug('No screen specified, using screen 0.')

    params['fps'] = 20
    import platform
    if platform.system() == 'Windows' or platform.system() == 'Linux':
        params['fps'] = 40

    ### Initialise content provider
    cp = ufContentProvider.ufContentProvider(params)
    cp.load()

    ### GUI
    if args.gui:
        logger.info('Starting gui')
        from multiprocessing import Process
        p = Process(target=gui)
        p.start()

    ### Main Event Loop
    from pygletScreenConsumer import pygletScreenConsumer as screenConsumer
    screenConsumer(contentProvider=cp, params=params)
