# How to Use Aesop's Table

Many of the features are currently live and working as intended. The first thing that should go out of date here is the Admin page, which I'm rushing to get properly setup.

## Creating a tournament
Creating a tournament, on the homepage there is a create tournament button. Enter the Title you want displayed for your tournament. This is currently un-editable, but that is something that I can fix for now, before I automate it. Once logins are implemented, you will need to be logged in to create a tournament.

## Registering players
Your tournament url with be something like aesopstables.net/# where the number is the ID for your tournament. This is probably the best link to send your players as it includes a button so they can register themselves. If they don't want to, you can click that button, or go to aesopstables.net/#/register to register players. Currently I am getting the ID list from [NRDB](https://netrunnerdb.com/), but have to manually call updates. If I'm missing an ID, do ping me.

## Admin page
I'm hoping to deprecate this ASAP, but for now all admin functions are available at aesopstable/#/admin. From there you can delete, drop, and edit players (the delete option is removed after you start the tournament so as to not delete games those players were in). Additionally there is a button to add/remove your tournament from the front page. For now there is no way other than the frontpage or knowing the url to get a tournament.

Once all your players are registered you can hit the start tournament button, which will pair the first round. Pairings urls follow the format aesopstables.net/#/#. To get acess to the admin section for pairing you append /admin at the end of that url. From there you can report results (it routes you back to the non-admin page, this will get fixed with login permissions), undo the pairings, and close the round.

## Undo Pairings & Close the Round
For now this deletes all pairings. If you hit the pairing button, it should make the same (or very similar) pairings. However the most likely reason you're undoing a pairing is because a result changed. In that case, change the result, then on the admin panel for any round but the one you were doing the pairing for, hit close round. That should recalculate everyone's scores. If you do hit close round on the current round after deleting all pairings, nothing bad will happen, but the round counter will go up one.

## Reporting Results
Eventually I want to automate this, but for now you can go to aesopstables.net/#.json to get an [ABR](https://alwaysberunning.net/) compatible json. Download that and upload it to there, and it should auto-populate everything. Contact me first if there is an issue, as it's more likely to be an issue on my end. 