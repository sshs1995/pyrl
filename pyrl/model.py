"""
Wrapper class for `PolicyGradient`.

"""
from __future__ import absolute_import, division

import imp
import os
import sys

from .               import configs
from .performance    import Performance2AFC
from .policygradient import PolicyGradient

class Model(object):
    def __init__(self, modelfile):
        # Load model specification as module
        try:
            self.m = imp.load_source('model', modelfile)
        except IOError:
            print("Couldn't load model file {}".format(modelfile))
            sys.exit()

        # Model specification
        self.spec = self.m

        # Task definition
        if 'Task' in vars(self.m):
            self.Task = self.m.Task
            self.task = self.m.Task()
        else:
            class Task(object):
                def __init__(_self):
                    setattr(_self, 'get_condition', self.m.get_condition)
                    setattr(_self, 'get_step',      self.m.get_step)

                    if 'terminate' in vars(self.m):
                        setattr(_self, 'terminate', self.m.terminate)
            self.Task = Task
            self.task = Task()

        # Fill in missing info
        self.config = {}
        for k in configs.required:
            if k not in vars(self.m):
                print("[ Model ] Error: {} is required.".format(k))
                sys.exit()
            self.config[k] = vars(self.m)[k]
        for k in configs.default:
            self.config[k] = vars(self.m).get(k, configs.default[k])

        # Inputs
        self.config['Nin']  = len(self.config['inputs'])

        # Outputs
        if 'Nout' not in self.config:
            self.config['Nout'] = len(self.config['actions'])

        # Ensure integer types
        self.config['n_gradient']   = int(self.config['n_gradient'])
        self.config['n_validation'] = int(self.config['n_validation'])

        # Performance measure
        if self.config['Performance'] is None:
            self.config['Performance'] = Performance2AFC

        # For online learning, make some adjustments.
        if self.config['mode'] == 'continuous':
            self.config['fix'] += ['states_0']
        if False and self.config['mode'] == 'continuous':
            if self.config['n_gradient'] != 1:
                print("Setting n_gradient = 1.")
                self.config['n_gradient'] = 1
            if self.config['baseline_split'] != 1:
                print("Setting baseline_split = 1.")
                self.config['baseline_split'] = 1

        # For trial-by-trial learning, decrease the learning rate
        if self.config['n_gradient'] == 1:
            #self.config['lr']          = 0.001
            #self.config['baseline_lr'] = 0.001
            #print("n_gradient = 1, decreasing learning rates to {}"
            #      .format(self.config['lr']))

            self.config['checkfreq'] = 1

    def get_pg(self, config_or_savefile, seed=1, dt=None, load='best'):
        return PolicyGradient(self.Task, config_or_savefile, seed=seed, dt=dt, load=load)

    def train(self, savefile, seed, recover=False):
        """
        Train the network.

        """
        if recover and os.path.isfile(savefile):
            pg = self.get_pg(savefile, load='current')
        else:
            self.config['seed']          = 3*seed
            self.config['policy_seed']   = 3*seed + 1
            self.config['baseline_seed'] = 3*seed + 2
            pg = self.get_pg(self.config, self.config['seed'])

        # Train
        pg.train(savefile, recover=recover)
