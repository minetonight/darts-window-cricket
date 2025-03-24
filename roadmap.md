) dark theme update
)) change the background color to something dark and update all the text colors to be visible on dark background

) the game counts the marks per player and the rounds

) the game shows the mpr marks per round next to the diff for each player 

) undo last mark button and undo last round button
)) keep in memory the order of the marks and create undo buttons
))) make sure the mpr and rounds are calculated accurately from that memory after undos

) save the game history in file at the end of each game - 'player name 1 vs player name 2 on date'.txt
)) the text file contains alternating lines with each player name and score for each round

) add ScreenManager and two Screens: data input and game screen
)) data input sets player 1 and player 2 names
)) data input sets highest scoring sector between 20 and 6, default is 20
))) and next to it is the lowest sector non editable that updates to "highest scoring sector"-5
)) data input sets bull is 25 points or bull is "highest scoring sector"+5
))) in the game screen show the value of the bull in brackets Bull[11 pts]
)) data input screen has start game button

) the sectors values and points are updated with values from the data input screen

) when the game ends, the next player button shows "new game?" text and leads to data input screen with the last game values preloaded
)) all necessary players game variables are reset with the start of a new game
