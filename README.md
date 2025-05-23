# OutputDatabaseAnalysis

## Introduction
The origin of this project was a desire to custom analyze chess games.
- I tried using Chessbase, SCID vs. PC, Arena, and VBA but nothing was as customizable or had the potential to be automated as I would have liked.
- I also found it difficult to output the numbers I wanted. I had grand ideas for how to use specific datapoints, but how to get them was a challenge.

## History
This project was effectively the first non-trivial Python project I ever attempted. It has morphed and changed quite a bit over the years (look at the Git history!), but it's turned into something reliable and meets the goal of what I was looking to achieve.

## Results
The output file is a tab-delimited text file with game (G) and move (M) records. Exact specifications can be found under the `/doc` directory of this repository.

## Usage
Do whatever you want with it. My use case has been to dump the results to a SQL database (repository [db_ChessWarehouse](https://github.com/chessking94/db_ChessWarehouse)) for statistical analyses.

## How-To
There are two ways to run this program:
- Use `config.json`. Populate the variables and go to town.
- Use the CLI. The program is built with `argparse` to override values defined in `config.json`. For assistance, run the command `python OutputDatabaseAnalysis.py -h` to see the options.
