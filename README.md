# Side Aware Swiss Software (SASS) and Aesop's Tables

## Overview

Currently this directory has two different, related, but now seperate projects in it. The App folder contains a python implementation of single sided swiss for netrunner. It runs as a command line interface tool, and reads writes outputs to csvs and jsons. I'm not intending to continue maintaining this, and it may disappear at some point in the future.

The second folder, named sass, is what runs [Aesop's Tables](http://aesopstables.net/). This is a Flask app that contects to a PostgreSQL database to run single sided swiss tournaments. This is main my development target. My current goal is getting close to, or exceeding current [Cobra](http://cobr.ai/) capabilities. The list of tasks, and my rough ordering of them can be found in projects tab.

I'm a novice, self taught coder, so would really appreciate suggestions/pull requests from anyone who wants to help.


## How the pairing algorithm works
At a high level, what this algorithm is finding the minimum weight graph where each player is a node, and each edge is the desirability of a given pairing. The weight on the edge is affected by the difference in the player's scores (ranking) and also the difference in the amount of games they've played with each side. The closer a pair's ranks are to each other the lower the score. Similarly if the players have no side bias (or opposite side bias) the cost of pairing them is 0. But if they have the same side bias, the cost increases (decreasing the likelyhood that they will get paired).
