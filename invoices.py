#!/home/sunbit/python2.7/bin/python
import json
import sys
from endesa import *
from gasnatural import *
from simyo import *
from sorea import *
from yoigo import *
from inspect import isclass
from copy import deepcopy
import datetime
import logging

logger = logging.getLogger('invoices')
hdlr = logging.FileHandler(os.path.expanduser('~/invoices.log'))
formatter = logging.Formatter('%(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

import warnings
warnings.filterwarnings("ignore")


def load_tasks():
    """
        Loads the tasks from disk
    """
    try:
        task_info = json.loads(open('{}/tasks.json'.format(sys.argv[0][:sys.argv[0].rfind('/')])).read())
    except:
        task_info = json.loads(open('tasks.json').read())
    return task_info['tasks'], {k: v for (k, v) in task_info.items() if k != 'tasks'}


def get_task_options(task, defaults):
    """
        Returns a copy of the defaults, updated with current task options
    """
    options = deepcopy(defaults)
    options.update(task['options'])
    options['logger'] = logger
    return options


def get_importers(locals):
    """
        Return all the classes that implement InvoiceImporter, indexed by class name attribute
    """
    return {klass.company: klass for (klassname, klass) in locals.items() if isclass(klass) and InvoiceImporter in klass.__bases__}


if __name__ == "__main__":

    logger.info("=" * 80)
    logger.info("\nInvoices importer log : {}\n".format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
    tasks, defaults = load_tasks()
    importers = get_importers(locals())
    debugging = False
    debug_filter = ''
    if len(sys.argv) >= 2:
        debugging = sys.argv[1] == 'debug'
        if len(sys.argv) >= 3:
            debug_filter = sys.argv[2]

    for task in tasks:
        if debugging and debug_filter and task['company'] != debug_filter:
            continue
        importer_klass = importers[task['company']]
        params = get_task_options(task, defaults)
        importer = importer_klass(**params)
        importer.login(debug=debugging)
        importer.save_invoices(debug=debugging)
