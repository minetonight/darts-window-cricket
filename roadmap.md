v   ) dark theme update
v   )) change the background color to something dark and update all the text colors to be visible on dark background
v   ) add font and nice checks for marks
v   ) make the fonts larger
v   ) the diff label must become 90% white 10% grayed
v   ) setup nice fonts

v   ) add vusual hit counter in sectors with dots, for current round only


v   ) the game counts the rounds
v   ) the game shows the mpr marks per round next to the diff for each player 
    )) mpr is with 2 decimals: 1.92, not 1.9
v   )) just the layout

    ) implement undo last mark button 
    )) add the appropriate method in the GameScreen class and connect them to the button using the on_release event.
    )) keep 2d arrays in memory with single marks with the order of the marks for each round 
    )) add_hit fills the arrays for the current round
    ))) make sure the mpr is calculated accurately from that memory after undos
    ))) update the all current round variables when a mark is undone
    
    ) implement undo last round button
    )) add the appropriate method in the GameScreen class and connect them to the button using the on_release event.
    )) undo all marks for the current player in the current round
    )) then undo all marks from the last round of the previous player
    )) track the rounds changes backwards and update accordingly
    )) visually and internally switch back to the previous player
    )) the previous player round start from scratch

    ) save the game history in file at the end of each game - 'player name 1 vs player name 2 on date'.txt
    )) the text file contains alternating lines with each player name and score for each round
    )) if there is history file, load the players names from the file in the data input screen

    ) replay game function
    )) from history file, call functions that add marks and switch players

v   ) add ScreenManager and two Screens: data input and game screen
v   )) text input sets player 1 and player 2 names
v   )) combobox sets highest scoring sector between 20 and 6, default is 20
v   ))) and next to it is the lowest sector non editable that updates to "highest scoring sector"-5
v   )) radioboxes sets bull is 25 points or bull is "highest scoring sector"+5
v   ))) in the game screen show the value of the bull in brackets e.g. "Bull[11 pts]"
v   )) data input screen has start game button
v   )) the sectors values and points given are updated with values from the data input screen
v   )) add switch positions button below players names, that swaps the texts in the two input fields

v    )) when the game ends, the next player button shows "new game?" text and leads to data input screen with the last game values preloaded
v   ))) all necessary players game variables are reset with the start of a new game

v   ) fix marks in more than three different sectors.
v   ) fix nine marks in nine sectors, as up to three sectors with nine marks total.
    )) add complex check for impossible cases of: {1x 20; 1x 19; 4x 18}
    promted and failed with:
    + "lets go to next level. how to add complex check for impossible cases of: {1x 20; 1x 19; 4x 18}. try to count also darts used and dont allow more than three darts"

    ) 