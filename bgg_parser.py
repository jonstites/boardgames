#!/usr/bin/env python3

import urllib                                       
from bs4 import BeautifulSoup
import argh
import sys
import re
from pprint import pprint

"""
Enables quick lookup and collection of board game information using BoardGameGeek.com
Requires beautifulsoup4 and argh packages.

Example Usage:
bgg_parser.py Eclipse "Mage Knight" "Dead of Winter" "Netrunner" "Betrayal at House on the Hill" \
"Pandemic" "Space Alert" -o "game_night_2015-10-17.txt" -a "Mage Knight:New game - have never played before" \
"Dead of Winter:New game - have never played before" "Eclipse:New game -have never played before" \
"Netrunner:Brandon and I each have a copy, so 4 people could be playing at once in two separate games"


"""



bgg_search_url = "https://boardgamegeek.com/geeksearch.php?action=search&objecttype=boardgame&q={0}&B1=Go"


@argh.arg("games", nargs="+")
@argh.arg("-a", "--additional_notes", nargs="+")
def main(games, additional_notes=None, output="/dev/stdout"):
    notes = get_notes(additional_notes)
    with open(output, 'w') as handle:
        print("Suggested Games: ", file=handle)
        template = "{0}.\t{1}"
        for i, game in enumerate(games):
            print(template.format(i+1, game), file=handle)

        for game in games:
            new_section(handle)
            game_format = game.replace(" ", "+")
            query = bgg_search_url.format(game_format)
            html_source = open_url(query)
            query_response = BeautifulSoup(html_source, "html.parser")
            top_match = get_top_match(query_response, game)
            top_url = "http://boardgamegeek.com" + top_match
            game_html = get_game_page(top_url)
            game_response = BeautifulSoup(game_html, "html.parser")
            player_num, play_time, rank, description = get_game_info(game_response)
            output_stats(
                game, player_num, play_time, rank, description, notes, 
                top_url, handle)

def new_section(handle):
    print("\n", "-"*70, "\n", file=handle)

def get_notes(additional_notes):
    d = {}
    if not additional_notes:
        return {}
    for note in additional_notes:
        key, value = note.split(":")
        d[key] = value
    return d

def output_stats(
        game, player_num, play_time, rank, description, notes, 
        top_match, handle):
    template = "Game: {0}\t{1}:\t{2}\n"
    print(template.format(game, "BGG URL", top_match), file=handle)
    print(template.format(game, "BGG Board Game Ranking", rank), file=handle)
    print(template.format(game, "Players", player_num), file=handle)
    print(template.format(game, "Play time", play_time), file=handle)
    print(template.format(game, "Description", description), file=handle)
    print(template.format(game, "Additional Notes", notes.get(game, None)), file=handle)

def get_game_page(top_match):
    html_source = open_url(top_match)
    return html_source

def get_game_info(game_response):
    player_num = get_player_number(game_response)
    play_time = get_suggested_playtime(game_response)
    rank = get_rank(game_response)
    description = get_description(game_response)
    return player_num, play_time, rank, description

def get_description(game_response):
    for meta in game_response.find_all("meta"):
        if meta["name"] == "description":
            soup = BeautifulSoup(meta["content"], 'html.parser').get_text()
            return soup.encode("UTF-8").decode("UTF-8").encode("ascii", "ignore").decode()

def get_rank(game_response):
    for data_entry in game_response.find_all("td"):
        for div in data_entry.find_all("div", class_="mf nw b"):
            text = div.get_text().strip().rstrip()
            if "Board Game Rank:" in text:
                for col in  text.split():
                    if col.isdigit():
                        rank = col
                        return rank

def get_suggested_playtime(game_response):
    time = game_response.find(id="edit_playtime")
    for div in time.find_all("div"):
        text = div.get_text().rstrip().strip()
        converted = text.encode("UTF-8").decode("UTF-8")
        if converted[:1].isdigit():
            return converted
    

def get_player_number(game_response):
    players = game_response.find(id="edit_players")
    for div in players.find_all("div"):
        text = div.get_text().rstrip().strip()
        converted = text.encode("UTF-8").decode("UTF-8")
        if converted[:1].isdigit():
            return converted
            
        
def get_top_match(query_response, game):

    game_table = query_response.find(id="results_objectname1")
    if not game_table:
        print("no item found matching {0}".format(game))
        sys.exit(2)
    top_match = game_table.a
    return game_table.a.get("href")

def open_url(url):
    with urllib.request.urlopen(url) as sock:
        html_source = sock.read()
    return html_source


if __name__ == "__main__":
    argh.dispatch_command(main)
