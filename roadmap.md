v   ) dark theme update
v   )) change the background color to something dark and update all the text colors to be visible on dark background


    ) the game counts the marks per player and the rounds
    ) the game shows the mpr marks per round next to the diff for each player 
v   )) just the layout

    ) implement undo last mark button and undo last round button
v   )) just the layout
    )) When you want to implement their functionality, we can add the appropriate methods in the GameScreen class and connect them to the buttons using the on_release event.
    )) keep in memory the order of the marks and create undo buttons
    ))) make sure the mpr and rounds are calculated accurately from that memory after undos

    ) save the game history in file at the end of each game - 'player name 1 vs player name 2 on date'.txt
    )) the text file contains alternating lines with each player name and score for each round
    )) if there is history file, load the players names from the file in the data input screen

v   ) add ScreenManager and two Screens: data input and game screen
v   )) text input sets player 1 and player 2 names
v   )) combobox sets highest scoring sector between 20 and 6, default is 20
v   ))) and next to it is the lowest sector non editable that updates to "highest scoring sector"-5
v   )) radioboxes sets bull is 25 points or bull is "highest scoring sector"+5
v   ))) in the game screen show the value of the bull in brackets e.g. "Bull[11 pts]"
v   )) data input screen has start game button
v   )) the sectors values and points given are updated with values from the data input screen
v   )) add switch positions button below players names, that swaps the texts in the two input fields

    )) when the game ends, the next player button shows "new game?" text and leads to data input screen with the last game values preloaded
    ))) all necessary players game variables are reset with the start of a new game

v   ) fix nine marks in nine sectors, as up to three sectors with nine marks total.
    )) add complex check for impossible cases of: {1x 20; 1x 19; 4x 18}

    ) add font and nice checks for marks