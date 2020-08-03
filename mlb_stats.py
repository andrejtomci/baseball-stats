#!/usr/bin/python3
# coding=utf-8

import urllib.request
from itertools import groupby
import collections
import re
import os

import click
from jinja2 import Environment, FileSystemLoader

PRINT_STRING = "maximálna séria výhier:{0:>2}; nastala:{1:>2}x; handicaps: {2:>2} <====> maximálna séria prehier:{" \
               "3:>2}; nastala:{4:>2}x; handicaps: {5:>2} "
MLB_TEAMS = dict(
    ("Los Angeles Dodgers", "http://www.baseball-reference.com/teams/LAD/2020-schedule-scores.shtml"),
    ("New York Yankees", "http://www.baseball-reference.com/teams/NYY/2020-schedule-scores.shtml"),
    ("Minnesota Twins", "http://www.baseball-reference.com/teams/MIN/2020-schedule-scores.shtml"),
    ("Atlanta Braves", "http://www.baseball-reference.com/teams/ATL/2020-schedule-scores.shtml"),
    ("Milwaukee Brewers", "http://www.baseball-reference.com/teams/MIL/2020-schedule-scores.shtml"),
    ("Miami Marlins", "http://www.baseball-reference.com/teams/MIA/2020-schedule-scores.shtml"),
    ("Tampa Bay Rays", "http://www.baseball-reference.com/teams/TBR/2020-schedule-scores.shtml"),
    ("Detroit Tigers", "http://www.baseball-reference.com/teams/DET/2020-schedule-scores.shtml"),
    ("Philadelphia Phillies", "http://www.baseball-reference.com/teams/PHI/2020-schedule-scores.shtml"),
    ("Cincinnati Reds", "http://www.baseball-reference.com/teams/CIN/2020-schedule-scores.shtml"),
    ("San Diego Padres", "http://www.baseball-reference.com/teams/SDP/2020-schedule-scores.shtml"),
    ("San Francisco Giants", "http://www.baseball-reference.com/teams/SFG/2020-schedule-scores.shtml"),
    ("Arizona Diamondbacks", "http://www.baseball-reference.com/teams/ARI/2020-schedule-scores.shtml"),
    ("Pittsburg Pirates", "http://www.baseball-reference.com/teams/PIT/2020-schedule-scores.shtml"),
    ("Colorado Rockies", "http://www.baseball-reference.com/teams/COL/2020-schedule-scores.shtml"),
    ("Boston Red Sox", "http://www.baseball-reference.com/teams/BOS/2020-schedule-scores.shtml"),
    ("Cleveland Indians", "http://www.baseball-reference.com/teams/CLE/2020-schedule-scores.shtml"),
    ("Chicago White Sox", "http://www.baseball-reference.com/teams/CHW/2020-schedule-scores.shtml"),
    ("Kansas City Royals", "http://www.baseball-reference.com/teams/KCR/2020-schedule-scores.shtml"),
    ("Oakland Athletics", "http://www.baseball-reference.com/teams/OAK/2020-schedule-scores.shtml"),
    ("Seattle Marines", "http://www.baseball-reference.com/teams/SEA/2020-schedule-scores.shtml"),
    ("Baltimore Orioles", "http://www.baseball-reference.com/teams/BAL/2020-schedule-scores.shtml"),
    ("Los Angeles Angels", "http://www.baseball-reference.com/teams/LAA/2020-schedule-scores.shtml"),
    ("Texas Rangers", "http://www.baseball-reference.com/teams/TEX/2020-schedule-scores.shtml"),
    ("Houston Astros", "http://www.baseball-reference.com/teams/HOU/2020-schedule-scores.shtml"),
    ("Toronto Blue Jays", "http://www.baseball-reference.com/teams/TOR/2020-schedule-scores.shtml"),
    ("Chicago Cubs", "http://www.baseball-reference.com/teams/CHC/2020-schedule-scores.shtml"),
    ("Washington Nationals", "http://www.baseball-reference.com/teams/WSN/2020-schedule-scores.shtml"),
    ("New York Mets", "http://www.baseball-reference.com/teams/NYM/2020-schedule-scores.shtml"),
    ("St.Louis Cardinals", "http://www.baseball-reference.com/teams/STL/2020-schedule-scores.shtml"),
)


def get_team_results(team_url):
    results = []
    loss_handicaps = 0
    win_handicaps = 0
    score = re.compile(r'\d+')

    # get html as string
    website = str(urllib.request.urlopen(team_url).read())
    body = website.split("</tbody>")[1]

    # split to matches
    matches = body.split("""<tr ><th scope="row" class="right " data-stat="team_game" >""")[1::]

    try:  # unplayed matches throw exception
        for match in matches:
            # determine win/loss
            result = (match.split("""<td class="left " data-stat="win_loss_result" >""")[1][0])
            results.append(result)
            win = result == "W"

            # determine score
            home_score_text = match.split("""data-stat="R" >""")[1]
            home_score = int(score.search(home_score_text).group())
            away_score_text = home_score_text.split("""data-stat="RA" >""")[1]
            away_score = int(score.search(away_score_text).group())

            # check handicaps
            if abs(home_score - away_score) > 1:
                if win:
                    win_handicaps += 1
                else:
                    loss_handicaps += 1

    except IndexError:  # unplayed match ends the loop
        pass

    return results, win_handicaps, loss_handicaps


def get_win_loss_streaks(results, result_char):
    # get sorted win/loss streaks
    streaks = sorted([len(list(g)) for k, g in groupby(results) if k == result_char], reverse=True)

    return streaks[0], streaks.count(streaks[0])


def mlb_stats():
    stats = {team: {} for team in MLB_TEAMS.keys()}

    for team, link in MLB_TEAMS.items():
        team_results, win_handicaps, loss_handicaps = get_team_results(link)
        max_win_streak, max_win_streak_count = get_win_loss_streaks(team_results, "W")
        max_loss_streak, max_loss_streak_count = get_win_loss_streaks(team_results, "L")
        stats.get(team).update(
            {"win_handicaps": win_handicaps, "loss_handicaps": loss_handicaps, "max_win_streak": max_win_streak,
             "max_win_streak_count": max_win_streak_count, "max_loss_streak": max_loss_streak,
             "max_loss_streak_count": max_loss_streak_count})

    return stats


def print_stats(stats):
    for team, team_stats in stats.items():
        to_print = PRINT_STRING.format(team_stats.get("max_win_streak"), team_stats.get("max_win_streak_count"),
                                       team_stats.get("win_handicaps"), team_stats.get("max_loss_streak"),
                                       team_stats.get("max_loss_streak_count"), team_stats.get("loss_handicaps"))
        print_length = len(("|{0:^25}|: {1}|\n".format(team, to_print)))
        print("|{0:-<{1}}|\n".format("", print_length - 3))
        print("|{0:^25}|: {1}|\n".format(team, to_print))


def fill_template(stats):
    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)

    template = env.get_template("mlb_stats.html")

    rendered_html = template.render(teams=stats)

    if not os.path.exists("public"):
        os.makedirs("public")
    with open("public/index.html", "w") as out_file:
        out_file.write(rendered_html)


@click.command()
@click.option("--template", is_flag=True)
def main(template):
    stats = mlb_stats()
    if template:
        fill_template(stats)
    else:
        print_stats(stats)


if __name__ == '__main__':
    main()
