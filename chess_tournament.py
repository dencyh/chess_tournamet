import asyncio
from datetime import datetime, timezone
import logging as log
from chessdotcom import get_player_profile, get_player_games_by_month, get_player_stats
from telegram import Update
from telegram.ext import ContextTypes
from settings import settings
import time

from utils import read_numbers_from_file, write_numbers_to_file


class ChessTournament:
    def __init__(self):
        self.nicks = ['🥦 Leha', 'Sanya 👹']
        self.players = ['makecash', 'dencyh']
        log.info(settings.db)
        print("***********", settings.db)
        self.score = read_numbers_from_file(settings.db)
        log.debug(self.score)
        self.waiting_for_names = settings.waiting_for_names
        self.confirmed = settings.confirmed
        self.started = False
        self.stopped = False
        self.before_season_timestamp = int(time.time())
        self.last_game_timestamp = 0
        self.total_games = 0
        self.current_set_score = [0, 0]
        self.best_of = 2
 

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

    def update_score(self) -> str:
        log.info('Updating score')
        response = 'No new games'

        today = datetime.now(timezone.utc)
        try:
            log.info(f'{self.players[0]}, {today.year}, {today.month}')
            games_response = get_player_games_by_month(self.players[0], today.year, today.month)
            log.debug(games_response)
        except Exception as e:
           log.error(e)
           return response

        if games_response and games_response.games:
            # define last game before the season
            games = games_response.games;
            if (not self.before_season_timestamp):
                self.before_season_timestamp = games[0].end_time

            # get array of the games from end_timestamp
            season_games = list(filter(lambda game: game.end_time > self.before_season_timestamp, games_response.games))
            if (not season_games):
                log.info('No Season Games yet')
                return response

            # ordered from old to recent
            new_games = list(filter(lambda game: game.end_time > self.last_game_timestamp, season_games))
            if (not new_games):
                log.info('No New Games')
                return response 

            for game in new_games:
                self.total_games += 1
                self.last_game_timestamp = season_games[-1].end_time
                log.debug(game)
                player1 = game.white if game.white.username == self.players[0] else game.black
                player2 = game.white if game.white.username == self.players[1] else game.black
                
                if (player1.username != self.players[0] or player2.username != self.players[1]):
                    response = 'Someone playing with Hindus'
                    log.info(f'Other game, player1 = {player1.username}, player2 = {player2.username}')
                    return response

                if player1.result == 'win':
                    self.current_set_score[0] += 1
                    response = f'Best of 3 score:\n{self.nicks[0]} {self.current_set_score[0]} - {self.current_set_score[1]} {self.nicks[1]}'
                elif player1.result == 'draw':
                    log.info("Draw")
                elif player2.result == 'win':
                    self.current_set_score[1] += 1
                    response =  f'Best of 3 score:\n{self.nicks[0]} {self.current_set_score[0]} - {self.current_set_score[1]} {self.nicks[1]}';
                set_ended = False
                # When Best of 3 is over
                if self.current_set_score[0] >= self.best_of:
                    self.score[0] += 1
                    self.current_set_score = [0, 0]
                    response = response + '\n\n' + self.get_score()
                    write_numbers_to_file(self.score[0], self.score[1], settings.db)
                elif self.current_set_score[1] >= self.best_of:
                    self.score[1] += 1
                    self.current_set_score = [0, 0]
                    response = response + '\n\n' + self.get_score()
                    write_numbers_to_file(self.score[0], self.score[1], settings.db)
                return response

    def get_score(self) -> str:
        #    return f'🥦 {self.players[0]} {self.score[0]} - {self.score[1]} {self.players[1]} 👹'
        return f'🏆 Season 3\n{self.nicks[0]} {self.score[0]} - {self.score[1]} {self.nicks[1]}'
