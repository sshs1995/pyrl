import imp
import os
import sys

import numpy as np

from pyrl          import utils
from pyrl.figtools import Figure

#=========================================================================================
# Files
#=========================================================================================

here   = utils.get_here(__file__)
parent = utils.get_parent(here)

paperpath = os.path.join(parent, 'paper')
timespath = os.path.join(paperpath, 'times')
figspath  = os.path.join(paperpath, 'work', 'figs')

modelname = sys.argv[1]

#=========================================================================================
# Figure
#=========================================================================================

w   = utils.mm_to_inch(174)
r   = 0.48
fig = Figure(w=w, r=r, axislabelsize=11, labelpadx=6, labelpady=6,
             thickness=0.9, ticksize=5, ticklabelsize=9, ticklabelpad=3)

x0 = 0.11
y0 = 0.18

w = 0.37
h = 0.71

DX = 0.12

fig.add('reward',  [x0, y0, w, h])
fig.add('correct', [fig[-1].right+DX, y0, w, h])

T = 100

#=========================================================================================

times = []
xall  = []
original   = [modelname]
additional = [modelname+'_s'+str(i) for i in [1000, 1001, 1002, 1003, 1004]]
for name in additional + original:
    # Training history
    datapath = os.path.join(parent, 'work', 'data', name)
    savefile = os.path.join(datapath, name+'.pkl')
    if not os.path.isfile(savefile):
        continue
    training_history = utils.load(savefile)['training_history']

    # Time
    timefile = os.path.join(timespath, name+'.txt')
    if os.path.isfile(timefile):
        times.append(np.loadtxt(timefile))

    #-------------------------------------------------------------------------------------

    if '_s' in name:
        color = '0.8'
        lw    = 1.25
    else:
        color = 'k'
        lw    = 1.75

    #-------------------------------------------------------------------------------------
    # Reward
    #-------------------------------------------------------------------------------------

    plot = fig['reward']

    ntrials   = []
    rewards   = []
    pcorrects = []
    for record in training_history:
        ntrials.append(record['n_trials'])
        rewards.append(record['mean_reward'])

        perf = record['perf']
        pcorrects.append(utils.divide(perf.n_correct, perf.n_decision))
    ntrials   = np.asarray(ntrials)/T
    rewards   = np.asarray(rewards)
    pcorrects = np.asarray(pcorrects)

    print(rewards)
    w1 = list(np.where(rewards == -1)[0])
    w2 = list(np.where(rewards > -1)[0])
    try:
        w1.append(w2[0])
    except IndexError:
        pass

    dashes = [5, 3]

    #plot.plot(ntrials[w1], rewards[w1], '--', color=color, lw=lw, dashes=dashes)
    plot.plot(ntrials, rewards, color=color, lw=lw)
    #plot.plot(ntrials, rewards, 'o', color=color, ms=6, mew=0)

    xall.append(ntrials)

    #-------------------------------------------------------------------------------------
    # Percent correct
    #-------------------------------------------------------------------------------------

    plot = fig['correct']

    #plot.plot(ntrials[w1], 100*pcorrects[w1], '--', color=color, lw=lw)
    plot.plot(ntrials[w2], 100*pcorrects[w2], color=color, lw=lw)
    #plot.plot(ntrials, 100*pcorrects, 'o', color=color, ms=6, mew=0)

plot = fig['reward']
plot.xlim(0, max([max(x) for x in xall]))
plot.ylim(-1.1, 1.1)
plot.xlabel(r'Number of trials ($\times$' + '{})'.format(T))
plot.ylabel('Reward per trial')

if len(times) > 0:
    mean = np.mean(times)
    sd   = np.std(times, ddof=1)
    plot.text_lower_right(r'{:.1f} $\pm$ {:.1f} mins'.format(mean, sd), dy=0.03,
                          fontsize=10, color=Figure.colors('green'))

plot = fig['correct']
plot.xlim(0, max([max(x) for x in xall]))
plot.ylim(35, 100)
plot.ylabel('Percent correct\n(decision trials)')

if modelname == 'romo':
    plot.hline(target, color=Figure.colors('red'), zorder=1)

#=========================================================================================

fig.save(path=figspath, name='fig_learning_'+modelname)
