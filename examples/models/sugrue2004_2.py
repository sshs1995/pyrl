"""
Dynamic foraging task, based on

  Matching behavior and the representation of value in the parietal cortex.
  L. P. Sugrue, G. S. Corrado, & W. T. Newsome, Science 2004.

  http://dx.doi.org/10.1126/science.1094765

"""
from __future__ import division

import numpy as np

from pyrl import tasktools

# Inputs
inputs = tasktools.to_map('FIXATION', 'L-R', 'L-G', 'R-R', 'R-G')

# Actions
actions = tasktools.to_map('FIXATE', 'SACCADE-LEFT', 'SACCADE-RIGHT')

# Trial conditions
colors       = [('R', 'G'), ('G', 'R')]
reward_rates = [(8, 1), (6, 1), (3, 1), (1, 1)]

# Durations
fixation  = 300
delay_min = 1000
delay_max = 2000
decision  = 600
tmax      = fixation + delay_max + decision

# Rewards
R_ABORTED = -1

# Training
n_gradient   = 5
n_validation = 0

#lr          = 0.002
#baseline_lr = lr

class Task(tasktools.Task):
    def __init__(self):
        self.choices     = []
        self.reward_rate = None
        self.decisions   = []

    def _new_block(self):
        # Number of trials in the next block
        while True:
            block_size = int(self.rng.exponential(120))
            if 100 <= block_size < 200:
                break
        self.block_size = block_size
        self.n_trials   = 0

        # Reward rates
        while True:
            reward_rate = tasktools.choice(self.rng, reward_rates)
            if self.reward_rate is None or self.reward_rate != reward_rate:
                break
        self.reward_rate = reward_rate

        if self.rng.randint(2) == 0:
            r_RED, r_GREEN = reward_rate
        else:
            r_GREEN, r_RED = reward_rate
        r_tot = r_RED + r_GREEN

        Z = 1/r_tot

        self.reward_rate_RED   = Z * r_RED
        self.reward_rate_GREEN = Z * r_GREEN

        self.r_RED   = 0
        self.r_GREEN = 0

    def start_session(self, rng):
        # Random number generator
        self.rng = rng

        # New block of trials
        self._new_block()

    def start_trial(self):
        # Bait rewards
        delta_reward = 0.3
        if len(self.decisions) == 0 or self.decisions[-1]:
            #if self.r_RED == 0:
            self.r_RED += delta_reward*1*(self.rng.uniform() < self.reward_rate_RED)
            #if self.r_GREEN == 0:
            self.r_GREEN += delta_reward*1*(self.rng.uniform() < self.reward_rate_GREEN)

    def generate_trial_condition(self, rng, dt, context={}):
        delay = context.get('delay')
        if delay is None:
            delay = tasktools.uniform(self.rng, dt, delay_min, delay_max)

        durations = {
            'fixation': (0, fixation),
            'delay':    (fixation, fixation + delay),
            'decision': (fixation + delay, tmax),
            'tmax':     tmax
            }
        time, epochs = tasktools.get_epochs_idx(dt, durations)

        return {
            'durations':  durations,
            'time':       time,
            'epochs':     epochs,
            'colors':     tasktools.choice(self.rng, colors),
            'rate-red':   self.reward_rate_RED,
            'rate-green': self.reward_rate_GREEN
            }

    def generate_trial_step(self, rng, dt, trial, t, a):
        #---------------------------------------------------------------------------------
        # Reward
        #---------------------------------------------------------------------------------

        epochs = trial['epochs']
        status = {'continue': True}
        reward = 0

        if t-1 in epochs['fixation'] or t-1 in epochs['delay']:
            if a != actions['FIXATE']:
                status['continue'] = False
                self.decisions.append(False)
                reward = R_ABORTED
        elif t-1 in epochs['decision']:
            if a in [actions['SACCADE-LEFT'] or actions['SACCADE-RIGHT']]:
                status['continue'] = False
                self.decisions.append(True)
                self.n_trials += 1

                consolation_R = 0#.05#1*(self.rng.uniform() < 0.1)
                consolation_G = 0#.05#1*(self.rng.uniform() < 0.1)

                # Available reward (red)
                if not (self.choices and self.choices[-1] == 'G'):
                    trial['income-R'] = self.r_RED
                else:
                    trial['income-R'] = consolation_R

                # Available reward (green)
                if not (self.choices and self.choices[-1] == 'R'):
                    trial['income-G'] = self.r_GREEN
                else:
                    trial['income-G'] = consolation_G

                L, R = trial['colors']
                if ((a == actions['SACCADE-LEFT'] and L == 'R')
                    or (a == actions['SACCADE-RIGHT'] and R == 'R')):
                    status['decision'] = 'RED'

                    if self.choices and self.choices[-1] == 'G':
                        #print("COD (G - > R)")
                        # Changeover delay
                        reward = 0
                    else:
                        reward = self.r_RED
                        if reward == 0:
                            reward = consolation_R
                        self.r_RED = 0
                    self.choices.append('R')
                    trial['choice'] = 'RED'
                else:
                    status['decision'] = 'GREEN'

                    if self.choices and self.choices[-1] == 'R':
                        #print("COD (R -> G)")
                        # Changeover delay
                        reward = 0
                    else:
                        reward = self.r_GREEN
                        if reward == 0:
                            reward = consolation_G
                        self.r_GREEN = 0
                    self.choices.append('G')
                    trial['choice'] = 'GREEN'
                trial['reward'] = reward

                # New block of trials
                if self.n_trials == self.block_size:
                    self._new_block()

        #---------------------------------------------------------------------------------
        # Input
        #---------------------------------------------------------------------------------

        u = np.zeros(len(inputs))
        if t not in epochs['decision']:
            u[inputs['FIXATION']] = 1
        if t in epochs['delay'] or t in epochs['decision']:
            L, R = trial['colors']
            u[inputs['L-'+L]] = 1
            u[inputs['R-'+R]] = 1

        #-------------------------------------------------------------------------------------

        return u, reward, status

class ContextUpdater(object):
    def __init__(self, perf, rng):
        self.perf = perf

    def update(self, status, a):
        pass

    def get_context(self, rng):
        return {}

class Performance(object):
    def __init__(self):
        self.choiceR   = []
        self.choiceG   = []
        self.rateR     = []
        self.rateG     = []
        self.decisions = []
        self.rewards   = []
        self.rewardR   = []
        self.rewardG   = []

    def update(self, trial, status):
        self.decisions.append('decision' in status)

        if self.decisions[-1]:
            self.rateR.append(trial['rate-red'])
            self.rateG.append(trial['rate-green'])
            self.rewardR.append(trial['income-R'])
            self.rewardG.append(trial['income-G'])
            self.rewards.append(trial['reward'])
            if status['decision'] == 'RED':
                self.choiceR.append(1)
                self.choiceG.append(0)
            else:
                self.choiceR.append(0)
                self.choiceG.append(1)

            #print("Available: R {}, G {}, Chose {}, Got {}"
            #      .format(self.rewardR[-1], self.rewardG[-1], status['decision'],
            #              self.rewards[-1]))

    @property
    def n_trials(self):
        return len(self.decisions)

    @property
    def n_decisions(self):
        return sum(self.decisions)

    def display(self):
        n_trials    = self.n_trials
        n_decisions = self.n_decisions
        print("  Prop. decision: {}/{} = {:.3f}"
              .format(n_decisions, n_trials, n_decisions/n_trials))
