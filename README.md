# NCAA 06 Promotion and Relegation
Script which promotes/relegates teams between power and group conferences

## Synopsis
This script attempts to implement a [system](https://en.wikipedia.org/wiki/Promotion_and_relegation) akin to what's found in English soccer/football leagues with demoting (relegating) bad teams from top divisions and promoting good ones to take their place.  For example from the 2022-2023 season, Virginia Tech (3-8) and Boston College (3-9) might be relegated to the AAC, while Tulane (12-2) and UCF (9-5) would be promoted to take their place in the ACC.  This (usually) keeps the level of competition in the top conferences high by replacing cakewalk teams with high performers from the bottom conferences.  Sometimes these promoted teams have staying power and become perennial conference contenders, other times they're on the chopping block the very next season and someone else gets a shot.

## Requirements
In order to use this script you'll need [Madden Xtreme DB Editor](https://www.footballidiot.com/forum/viewtopic.php?t=21400)

If you're not using the *Folder* memcard type in PCSX2 you may also need:

* [PS2 Save Builder](https://www.ps2savetools.com/download/ps2-save-builder/)
* [mymc](http://www.csclub.uwaterloo.ca:11068/mymc/)

And until I get this into a self-contained binary, you'll need [python](https://www.python.org/downloads/) to run this.

## How To Use
There's a couple of steps in the process to perform the promotion/relegation dance.  But first, a disclaimer...

**Warning** This, like any other save modification, can and will brick your save!  Be sure to _backup_ your save before starting this process.  You have been warned...

This process should be done with a save that's been advanced to the off-season (post-bowls/champ) but before Budgets have been set.  In theory, this can be done anytime before advancing to the next season, but conference prestige does affect recruiting so it makes the most sense to do as early as possible in the off-season.

First thing you'll need to do is export some tables to CSV from your dynasty db contained in your save.  You'll do this by opening the db in *Madden Xtreme DB Editor*. (If you need help with getting to the DB file there are plenty of resources available, but [this](https://forums.operationsports.com/forums/showpost.php?p=2047976483&postcount=2) should get you there if you're not using the *folder* memcard type.  Folder users can navigate into the memcard folder and open the `BALSUSXXXXX` file directly)

1. CONF**
2. DIVI**
3. COCH
4. TEAM
5. TSWP

**Note: You'll only need to extract these tables once for your dynasty as they shouldn't change year to year.  The other three are required every year.

Next, you'll want to make a note of where you saved those CSV files, and by note I mean open up something like Notepad and put the [absolute path](https://en.wikipedia.org/wiki/Path_(computing)#Absolute_and_relative_paths) to each CSV file.  If someone wants to power through [tkinter](https://docs.python.org/3/library/tkinter.html) and make a GUI this step may become less complicated, but damnit Jim I'm an SRE not a UX developer so you'll need to paste the paths to the files when prompted without the help of a file dialog.

Now you can finally fire up the script by either double clicking the `relegate.bat` on windows or running `python relegate.py`.  It will prompt you for the paths to the aforementioned CSV files and ask how many teams per power conference you'd like to relegate.  Once you've done that, the script will automatically update the `TEAM` and `TSWP` csv files based on the season's records for the teams and display the changes that were made.

Finally, you'll need to import `TEAM` and `TSWP` into your dynasty via Madden Xtreme DB Editor (and PS2 Save Builder/mymc if you need it).  Once your import is done you should be able to fire up the game and validate that the conference members have been updated.

## Limitations
The biggest limitation to mention is that the `TSWP` table has a maximum of *446* entries.  Unfortunately this means there's a shelf life for this script.  Once you hit that limit, you won't be able to perform any more team swaps.  At most, you'll be able to use this script for *89* seasons assuming 1 team relegated per power conference.  This drops to *44* if you decide on 2 teams relegated per conference, *29* for 3 and so on.  Of course you can get creative about how you can work around this (only relegate if there's a winless power 5 team or undefeated group of 4, relegate every other season, etc).  Note, if you swap teams via other means (Pre-Dynasty team swaps for example) this will count against that 446 max and reduce the amount of seasons you can use this script for.

These next limitations reflect the current state of the script itself and some design decisions.  They may change over time and this section will be updated to reflect new/changed features.

In NCAA Next, there are 5 *power* conferences (ACC, B1G, Big 12, Pac-12, SEC) and 4 *group* conferences (AAC, C-USA, Mt West, Sun Belt).  Because this mismatch in the number of conferences exists the script dumps all promoted and relegated teams into a pool and randomly assigns them to new conferences.  This can lead to some strange conference rosters later on, I've had Boise St end up in the ACC and Alabama in the Mt West.

Independents are not considered currently.  Because they share a prestige value with the power conferences there's no real value in including them in the process as there are plenty of landing spots for group of 4 teams being promoted.

C-USA sucks.  No really, they take the place of the Sun Belt in vanilla as the only conference with a prestige of *1*.  As I mentioned before, this affects the quality of recruits that are interested in your program in addition to your team's prestige ([Playbook Gamer's](https://www.youtube.com/@PlaybookGamer) video on offseason recruiting highlights this issue).  When I was doing this manually in NCAA 08 I modified the WAC to 1 prestige and had two tiers of promotion/relegation so the truly awful teams ended up in the Sun Belt or WAC.  However, with the current randomization functionality, a few unlucky power teams might end up dropping down two levels of prestige instead of one which will make recruiting enough talent to promote and stay in a power conference more challenging.

## Future Considerations

It might be nice to have the script prompt the user for conference associations.  For example, the Big 12 and the SEC might both be tied to Sun Belt, ACC to the AAC, B1G to C-USA, and Pac-12 to Mt West.  In lieu of this, being able to dynamically choose a landing spot based on team geolocation rather than conference tie in might make more sense.

Either adjusting the C-USA prestige to align with the other group conferences or dropping another one down and doing two tiers of relegation would balance the conference prestiges.

Exporting the CSVs and asking for 5 paths each run is tedious and error prone.  Being able to directly interact with the DB file, removing the dependence on the DB editor, would improve the overall experience.

Coaching carousel mod tie-in, automatically fire coaches on relegated teams.  Not sure how this is wired in yet, might not be possible.

This script is created and tested for [NCAA Next](https://www.ncaanext.com/)  Additional work may allow for this to work with vanilla and/or other versions of NCAA football