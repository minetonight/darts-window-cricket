v   ) dark theme update
v   )) change the background color to something dark and update all the text colors to be visible on dark background
v   ) add font and nice checks for marks
v   ) make the fonts larger
v   ) the diff label must become 90% white 10% grayed
v   ) setup nice fonts

v   ) add vusual hit counter in sectors with dots, for current round only

v   ) the game counts the rounds
v   ) the game shows the mpr marks per round next to the diff for each player 
v   )) mpr is with 2 decimals: 1.92, not 1.9
v   )) just the layout

v   ) implement undo last mark button 
v   )) add the appropriate method in the GameScreen class and connect them to the button using the on_release event.
v   )) keep smth in memory with single marks with the order of the marks for each round 
v   )) add_hit fills the arrays for the current round
v   ))) make sure the mpr is calculated accurately from that memory after undos
v   ))) update the all current round variables when a mark is undone
    
v   ) implement undo last round button
v   )) add the appropriate method in the GameScreen class and connect them to the button using the on_release event.
v   )) undo all marks for the current player in the current round
v   )) then undo all marks from the last round of the previous player
v   )) track the rounds changes backwards and update accordingly
v   )) visually and internally switch back to the previous player
v   )) the previous player round starts with all marks from that round

v   ) save the game history in file at the end of each game - 'player name 1 vs player name 2 on date'.txt
v   )) that files must be accessible in the android memory, set permissions and appropriate file path.
v   ))) make it work on android
v   )) the text file contains the marks history data structure serialized in human readable form. ---alternating lines with each player name and score for each round---
v   )) if there is a history file, load the latest players names from the file to the data input screen
v   )) read history as text in the app
v   )) files are sorted by modification time

v   ) replay game function
v   )) from history file, call functions that add marks and switch players

v   ) add ScreenManager and two Screens: data input and game screen
v   )) text input sets player 1 and player 2 names
v   )) combobox sets highest scoring sector between 20 and 6, default is 20
v   ))) and next to it is the lowest sector non editable that updates to "highest scoring sector"-5
v   )) radioboxes sets bull is 25 points or bull is "highest scoring sector"+5
v   ))) in the game screen show the value of the bull in brackets e.g. "Bull[11 pts]"
v   )) data input screen has start game button
v   )) the sectors values and points given are updated with values from the data input screen
v   )) add switch positions button below players names, that swaps the texts in the two input fields

v   )) when the game ends, the next player button shows "new game?" text and leads to data input screen with the last game values preloaded
v   ))) all necessary players game variables are reset with the start of a new game

v   ) fix marks in more than three different sectors.
v   ) fix nine marks in nine sectors, as up to three sectors with nine marks total.


v   ) UI improvements
v   )) home screen: lowest sector: was too crammed
v   )) sectors to have larger fonts (except Bull)
v   )) narrow diff font: (+100) overflows 
    
v   ) replays to stay until exit button is pressed
v   )) replays have speed setting and pause button

v   ) history revamp
v   )) use json files, read txt too
v   )) file name as [rounds] [player1]{mpr1} vs [player2]{mpr2} on [date].json
v   )) text mode shows round and mpr
v   )) text mode shows history on one line

v   ) add player stats button
v   )) group players by name 
v   )) have history for wins, 
v   )) avg min and max rounds, 
v   )) avg min and max mprs, 
v   )) sectors stats, 
v   )) delete button for test replays.

v   ) export game files locally
v   )) android does not ask for permissions

    ) add complex check for impossible cases of: {1x 20; 1x 19; 4x 18}
    promted and failed with:
    + "lets go to next level. how to add complex check for impossible cases of: {1x 20; 1x 19; 4x 18}. try to count also darts used and dont allow more than three darts"


~  )) replays: add step forward and step backwards buttons, that are enabled when a replay is paused
   ))) - does not remove checkmarks from older rounds.
   ))) - I dont see the tick marks disappearing going backwards. 
   ))) - I dont see the marks dots appear all at once and disappear one by one going backwards.
        

    ) between undo buttons add abort match icon that leaves the current game and updates the metadata and saves a game file with name starting with aborted
    )) add continue aborted matches on homescreen that loads list of aborted game and lets you pick.
    ))) the list have back, delete and continue buttons below.

    ) bugfixes:
v   )) 3.0.0 - undo opponents turn was adding extra phantom scores.
v   )) 3.0.0 - replay end kicks you out to homescreen, not to history
v   )) double tap to use a list item in replays or stats
v   )) read text - "list index out of range" on my phone, for non-first file. Depends on export feature
v   )) sort the files by the date and time written in the filenames

