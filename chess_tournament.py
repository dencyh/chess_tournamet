import asyncio
from datetime import datetime, timezone
import logging as log
from chessdotcom import get_player_profile, get_player_games_by_month, get_player_stats
from telegram import Update
from telegram.ext import ContextTypes
from settings import settings
import time
import pandas as pd
from datetime import datetime

from utils import read_numbers_from_file, write_numbers_to_file


class ChessTournament:
    def __init__(self, start_datetime: str):
        self.nicks = ['🥦 Leha', 'Sanya 👹']
        self.players = ['makecash', 'dencyh']
        log.info(settings.db)
        # self.score = read_numbers_from_file(settings.db)
        self.score = [0, 0]
        log.debug(self.score)
        self.waiting_for_names = settings.waiting_for_names
        self.confirmed = settings.confirmed
        self.started = False
        self.stopped = False
        self.before_season_timestamp = datetime.fromisoformat(start_datetime).timestamp()
        self.last_game_timestamp = 0
        self.total_games = 0
        self.current_set_score = [0, 0]
        self.best_of = 2
        self.all_games = []
        log.info("Tournament created")
 
    def write_games_to_excel(self, games, file_name='games.xlsx'):
        data = []
        best_of_3_count = [0, 0]  # [wins by player1, wins by player2]
        set_results = []  # To store best of 3 results
        
        for i, game in enumerate(games):
            if game.white.username not in self.players or game.black.username not in self.players:
                continue
            if game.end_time <= self.before_season_timestamp:
                continue

            player1_game = game.white
            player1 = game.white.username
            player2 = game.black.username
            player2_game = game.black
            player1_nick = self.nicks[self.players.index(player1)]
            player2_nick = self.nicks[self.players.index(player2)]
            
            # Determine who won
            if game.white.result == "win":
                winner = player1
                best_of_3_count[self.players.index(player1)] += 1
                reason = player2_game.result
            elif game.black.result == "win":
                winner = player2
                reason = player1_game.result
                best_of_3_count[self.players.index(player2)] += 1
            else:
                reason = player2_game.result
                winner = "Draw"

            end_time = datetime.utcfromtimestamp(game.end_time).strftime('%Y-%m-%d %H:%M:%S')
            
            black_player = game.black.username
            white_player = game.white.username
            black_nick = player1_nick if black_player == player1 else player2_nick
            white_nick = player1_nick if white_player == player1 else player2_nick
            
            game_data = {
                "player1": player1,
                "player2": player2,
                "date and time": end_time,
                "black": black_player + " (" + black_nick + ")",
                "white": white_player + " (" + white_nick + ")",
                "who won": winner,
                "reason": reason
            }

            data.append(game_data)

            # Check if a Best of 3 set is concluded
            if best_of_3_count[0] >= self.best_of or best_of_3_count[1] >= self.best_of:
                set_winner = self.players[0] if best_of_3_count[0] > best_of_3_count[1] else self.players[1]
                set_results.append(f"Best of 3 won by {set_winner}")
                best_of_3_count = [0, 0]  # Reset the count
            else:
                set_results.append("")

        df = pd.DataFrame(data)
        df['set result'] = pd.Series(set_results)  # Add best of 3 results to the DataFrame
        
        df.to_excel(file_name, index=False)

    def set_challengers(self, msg: str) -> str:
        log.info('Settings challengers')

        names = msg.split(',')
        self.players[0] = names[0]
        self.players[1] = names[1]
        self.waiting_for_names = False

        player1 = get_player_profile(self.players[0])
        player1_stats = get_player_stats(self.players[0])
        player2 = get_player_profile(self.players[1])
        player2_stats = get_player_stats(self.players[1])

        log.debug(f'Player 1  - {player1.json}\nStats: {player1_stats.json}')
        log.debug(f'Player 2  - {player2.json}\nStats: {player2_stats.json}')

        response = f'Challengers are: {self.players[0]} and {self.players[1]}.\nConfirm? - Yes/No'
        log.info(response)
        return response
    
    def init_update(self) -> str:
        current_date = datetime.now(timezone.utc)
        start_date = datetime.fromtimestamp(self.before_season_timestamp, timezone.utc)
        current_year, current_month = current_date.year, current_date.month
        year, month = start_date.year, start_date.month

        self.all_games = []
        while (year < current_year) or (year == current_year and month <= current_month):

            all = get_player_games_by_month(self.players[0], year, month)
            self.all_games.extend(all.games)
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

        return self.update_score()

    def update_score(self, today: datetime = datetime.now()) -> str:
        log.info('Updating score')
        response = 'No new games'

        if self.all_games:
            # Filter games that happened after the season started
            season_games = list(filter(lambda game: game.end_time > self.before_season_timestamp, self.all_games))
            if not season_games:
                log.info('No Season Games yet')
                return response

            # Filter games that are new since the last checked game
            new_games = list(filter(lambda game: game.end_time > self.last_game_timestamp, season_games))
            if not new_games:
                log.info('No New Games')
                return response 

            for game in new_games:
                self.last_game_timestamp = max(self.last_game_timestamp, game.end_time)  # Update the last game timestamp to the most recent
                player1 = game.white
                player2 = game.black

                if (game.black.username == self.players[0]):
                    player1 = game.black
                    player2 = game.white
                
                # Skip if a third party is involved
                if player1.username not in self.players or player2.username not in self.players:
                    log.info(f'Other game detected, players were {player1.username} and {player2.username}')
                    continue

                # Update current set score based on the game result
                if player1.result == 'win' and player1.username == self.players[0]:
                    self.current_set_score[0] += 1
                elif player2.result == 'win' and player2.username == self.players[1]:
                    self.current_set_score[1] += 1

                # Check if the Best of 3 set has ended
                if self.current_set_score[0] >= self.best_of:
                    self.score[0] += 1
                    self.current_set_score = [0, 0]  # Reset current set score
                    response = f'Best of 3 set won by {self.nicks[0]}.\n {self.get_score()}'
                elif self.current_set_score[1] >= self.best_of:
                    self.score[1] += 1
                    self.current_set_score = [0, 0]  # Reset current set score
                    response = f'Best of 3 set won by {self.nicks[1]}.\n {self.get_score()}'

        self.write_games_to_excel(self.all_games)
        write_numbers_to_file(self.score[0], self.score[1], settings.db)  # Write the overall score to file
        return response

    def get_score(self) -> str:
        #    return f'🥦 {self.players[0]} {self.score[0]} - {self.score[1]} {self.players[1]} 👹'
        return f'🏆 Season 3\n{self.nicks[0]} {self.score[0]} - {self.score[1]} {self.nicks[1]}'
