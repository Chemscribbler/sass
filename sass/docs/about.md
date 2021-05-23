# About

# Why Singled Sided Swiss
## Short Summary

* Swiss is a nice format for maximizing the number of games everyone plays
* Double sided swiss always leads to scenarios where there is an incentive to play **fewer** games
* Single sided swiss keeps the good elements of the swiss format, encourages virtually all games will be played
* Still ensures everyone plays their decks evenly

## The Current State (Summer 2021)
From release through the present, Netrunner has primarily used double sided swiss as its format for running public tournament. Swiss tournaments means in each round every active player is paired against an opponent. Players are assigned opponents based on the amount of wins they've received so far, such that they're usually playing people with the same overall record.

### Double Sided Swiss
Netrunner has historically used Double Sided Swiss, where everyone plays both of their decks against each opponent (in theory, see problems below). So a match has two discreet games of Netrunner in it. Players are awarded points based on the outcome of each individual game. After a certain number of rounds the top N players go into a top cut, which is run as a double elimination bracket. At that point everyone else is done playing, and those 4/8/16 players compete for the top spot. This ends up meaning that the Swiss section is not used to determine final standings (though it does seed the top N), and instead serves as a gating function. The general perception is that seeding does not have a huge impact on the final result, though I'll admit to that particular issue being somewhat less discussed.

### Problems with Double Sided Swiss
As mentioned above, the Swiss into top cut ends up gating peoples performances, and ends up making a gating for what records will be sufficient to make it through to the cut and have a chance to win. For many large events, this record is explicit, for others there is an implicit cutoff. This can be undersirable for many reasons (it's opaqueness to new players should not be understated).

This gating issue becomes particularly problematic in swiss systems because people are matched against people with a similar record. This means that toward the end of the tournament, if say players cannot lose more than X games, every player (called Alex for this example) that has already lost X games will be paired against another player (called Blake) who has also lost X games. If you assume both games are a 50:50 for either player winning, 25% of the time Alex will make it to the cut, 25% Blake will, and 50% of the time they'll both win one of the two games, so neither of them make it into the cut. For both Alex and Blake, they have a higher chance of making the cut if they agree to 2-4-1. Instead of playing both games in their match, Alex and Blake will play the first game, and whoever loses will conceede the second game, guranteeing the other person has enough points to make it through the cut (the loser of the first match already has been eliminated so loses nothing). This means a subset of the players in the top cut will have records with some number of wins, some of which they did not "earn". This distorts placing, and also makes early rounds very impactful relative to later ones.

### Single Sided Swiss Solutions
The main advantage of single sided swiss is that the meta-game element of 2-4-1s is removed. This essentially means the outcome of every game should matter to every player, and meta-gaming the tournament structure should happen in exceedingly rare cases. This reduces the knowledge one needs to have to participate in a tournament, and should better ensure players earn their way to the top cut.

# Algorithm

This algorithm is based on an old paper for a chess algorithm, hacked heavily along the way. The basic idea is you make a [graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)) where each player is a node. Then two edges are drawn between every player, with a weight applied to each edge. That weight is determined by the function:
<p style="text-align: center;"><i>Cost = Score Cost + Side Cost</i></p>

If two players have already played one set of decks against each other (say Alex has played their corp deck against Blake) that edge is removed from the graph. This way if people have played twice against an opponent, they cannot be paired again. Then an [algorithm](https://en.wikipedia.org/wiki/Blossom_algorithm) is used to find the lowest possible total graph weighted sum of pairs.

The score cost is calculated as follows:
<p style="text-align: center;"><i>Score Cost = (A<sub>score</sub>-B<sub>score</sub>) * (A<sub>score</sub>-B<sub>score</sub> + 1)/2</i></p>

If player A and B have opposte side biases, the <i>Side Cost</i> is 0, otherwise it is
<p style="text-align: center;"><i>
Side Cost = 8<sup> max(pre-match bias, post-match bias)</sup>
</i></p>
Where the pre-match bias is the sum of their two biases before the playing the match, and post-match is their biases after the potential match.

<br/><br/>
# Hand Algorithm

If something breaks, or you want to do this by hand, you can do the following:

* Write everyone's names on slips of paper (or anything you can small pile shuffle)
* Record people's record and sides they've played
* On odd rounds (1,3,5, etc.) everyone will have played their decks the same number of times (with the exception of players who have recieved a bye), for this, pair normally
    * Shuffle all players in a score group (with the same number of wins)
    * Stack them in descending order (highest ranked player on top)
    * Deal out the top two cards. If they have not played each other at all, flip a coin to determine who corps. If they've already played once, pair them for the opposite sides. If they've already played twice, leave for now, and continue until you've paired the whole deck.
    * After dealing out all the players, if there are any people who cannot play, try to make the minimum number of swaps to have all matches paired.
* On even rounds (2,4,6, etc.)
    * Divide into two piles, those who have Corp'd +1 times, and those how have Run +1 times
    * Within each pile, sort them by strength descending, then shuffle within the score group
    * Grab the top card from each stack, that is the first pair. Then grab the second pair and repeat the process until all players are paired.
    * If any matches are disallowed, try to make the fewest possible swaps to get everyone a legal match
* If there are an odd number of players, the last player remaining the deck gets a bye. For the even rounds this may not be the lowest scoring player, due to the fact that the lowest scoring player may be in the smaller stack.
* For even rounds, if a player is neutral, because they've recieved a bye, put them in the smaller stack. If both stacks are even in size, randomly place them in one stack or the other.

# Attribution

* Developed primarily by Jeff "Ysengrin" Pruyne
* Built using Python/Flask/Jinja/PostgreSQL
* Would love any contributions/feedback
* For source code see [the github](https://github.com/Chemscribbler/sass)
* To contact Discord (Ysengrin#2501)/Stimslack for quick response if needed