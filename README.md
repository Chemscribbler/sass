# Side Aware Swiss Software (SASS)

## A tournament manager app designed for single sided swiss Netrunner tournaments

This app is meant to be an interactive application for tournament managers to seamlessly run single sided (or double sided if they're feeling perverse).

What I'm looking to do:

Currently I've got a very simple system set up where I can run single CLI commands to run a tournament. It imports pairings (potentially including tables and results) from a json. It also export a pairings json and a standings json. The standings json also contains all the info about pairings and tables.

Things I would like to do:
- Have a basic web interface to allow someone to run a tournament (real paint the rest of the owl shit here)
- Store tournament data in some sort of database- and have the front-end communicate with that (though maybe this isn't necessary and tournaments could be run in memory... but from the little I know this sounds bad)
- Improve my backend to be cleaner and easier to tinker with

I don't really know any web dev or database stuff. Trying to teach myself a little. So I'd be happy with help ranging from drawing some boxes and saying use this tool, to being a person I can bug with questions, to just doing full pull requests/development. If someone wants to help develop I'm happy to write up more specs/user stories, otherwise the best thing would be some people I could ask questions to.

My current plan would be to try and build out a simple app using Flask and HTML/CSS to do all my front end stuff, figure out some way to convert my app that's running in memory to working with a database.


## Current Outline

Right now a simple python app exists that can import and export jsons in a particular format (closely matching [cobra's](http://cobr.ai/)).
It does this using a custom Tournament class. In every tournament there is a dictionary of players (each made of a Player class). Every round goes into a round
dictionary and contains some admin info about the round and a dictionary of Tables (the final class).

The notable functions right now are:
- Tournament.add_player(name, corp_id*, runner_id*)
- Tournament.pair_round()
- Tournament.report_result(table_id, c_score, r_score, round*)
- Tournament.export_standings()

To run a tournament you use add_players, start_tournament, pair_round, report_result, and close_round. Can use import_pairings, potentially with the overwrite, to report pairings. 


## How the pairing algorithm works
At a high level, what this algorithm is finding the minimum weight graph where each player is a node, and each edge is the desirability of a given pairing. The weight on the edge is affected by the difference in the player's scores (ranking) and also the difference in the amount of games they've played with each side. The closer a pair's ranks are to each other the lower the score. Similarly if the players have no side bias (or opposite side bias) the cost of pairing them is 0. But if they have the same side bias, the cost increases (decreasing the likelyhood that they will get paired).
