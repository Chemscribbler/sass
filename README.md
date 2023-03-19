# Side Aware Swiss Software (SASS) and Aesop's Tables

## Overview

sass, is what runs [Aesop's Tables](http://aesopstables.net/). Due to hosting costs/buggy connections I don't keep this up all the time, working on fixing both of those, but reach out to me (Ysengrin on Discord/Slack) if you want me to boot it up. This is a Flask app that contects to a SQL database to run single sided swiss tournaments. This is main my development target. My current goal is getting close to, or exceeding current [Cobra](http://cobr.ai/) capabilities. The list of tasks, and my rough ordering of them can be found in projects tab.

I'm a novice, self taught coder, so would really appreciate suggestions/pull requests from anyone who wants to help.

## Installation and Running
To install download the package and make sure you have a Python 3.8 or better. Navigate to the folder where you have the downloaded file in a command line interface and run the following commands:

`python -m venv venv` - *this creates a virtual environemnt so anything you install won't disturb your main installation* - you should only have to do this once.

Then you'll need to activate the virtual environemnt - this is slightly OS dependant [see this](https://python.land/virtual-environments/virtualenv#Python_venv_activation) -- *you'll need to activate your environment once each time you open your terminal*
the run

`pip install -r requirements.txt` -- *this installs the required python libraries this package uses. You'll only need to do this once.*

Then with everything installed you should be all set. Every time you want to run the app you'll use

`flask run`. You're terminal will give you a local IP address, and if you paste that into your web browser the site will be accessible from your computer.

To update the legal identities you will need to delete the `ids.json` file. When you start up the server it should regenerate them. If it doesn't you can open up your terminal, enter a python session, and import `sass.tournament as t` and then run `t.get_ids()` and it should generate a new one.


## How the pairing algorithm works
At a high level, what this algorithm is finding the minimum weight graph where each player is a node, and each edge is the desirability of a given pairing. The weight on the edge is affected by the difference in the player's scores (ranking) and also the difference in the amount of games they've played with each side. The closer a pair's ranks are to each other the lower the score. Similarly if the players have no side bias (or opposite side bias) the cost of pairing them is 0. But if they have the same side bias, the cost increases (decreasing the likelyhood that they will get paired).
