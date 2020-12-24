from sportsreference.nfl.teams import Teams
import pandas as pd
from urllib.error import HTTPError

# read TheBaller Discord token
def load_token(token_file='./token'):
    with open(token_file, "r") as file:
        token = file.read()
        return token

def columnize(l, cols=3):
    tracker = dict()
    for ndx, s in enumerate(l):
        s = str(s)
        cur_s = tracker.get(ndx % cols, len(s))
        if len(s) > cur_s:
            tracker[ndx % cols] = len(s)
        else:
            tracker[ndx % cols] = cur_s
    return tracker

def cprint(string_list, cols=2, sep="  "):
    '''
    Function to print long lists more compactly.
    Uncomment the comments to have it print perfect columns in terminal.
    Unfortunately doesn't translate to Discord.

    ::string_list List[Str]:: list of strings
    ::cols Int:: number of columns to break up
    ::spaces Int:: number of spaces to add between words
    
    Returns: [Str]
    '''
    max_length = columnize(string_list, cols=cols)
    s = f"```{str(string_list[0]).ljust(max_length[0])}"
    for ndx, site in enumerate(string_list[1:]):
        site = str(site)
        column = (ndx + 1) % cols
        if column == 0:
            s += f"\n{site.ljust(max_length[0])}"
        else:
            s += f"{sep}{site.ljust(max_length[column])}"
    return s + "```"

def cprint_df(df):
    '''
    Similar to cprint above but takes a Pandas dataframe and returns a string to print the dataframe in Discord

    ::df pandas.DataFrame:: Pandas dataframe to print in Discord chat
    '''
    df_list = list(df.columns)
    num_cols = len(df_list)
    for row in df.to_numpy():
        df_list += list(row)
    df_no_nulls = list(map(str, map(remove_none_games, df_list)))
    return cprint(df_no_nulls, num_cols)

nfl_map = {"Tennessee Titans": "OTI","Kansas City Chiefs": "KAN","Green Bay Packers": "GNB","Seattle Seahawks": "SEA","Buffalo Bills": "BUF",
            "Baltimore Ravens": "RAV","Tampa Bay Buccaneers": "TAM","Indianapolis Colts": "CLT","New Orleans Saints": "NOR","Arizona Cardinals": "CRD",
            "Las Vegas Raiders": "RAI","Cleveland Browns": "CLE","Pittsburgh Steelers": "PIT","Minnesota Vikings": "MIN","Atlanta Falcons": "ATL",
            "Miami Dolphins": "MIA","Los Angeles Rams": "RAM","Dallas Cowboys": "DAL","Detroit Lions": "DET","San Francisco 49ers": "SFO",
            "Los Angeles Chargers": "SDG","Carolina Panthers": "CAR","Houston Texans": "HTX","Chicago Bears": "CHI","Philadelphia Eagles": "PHI",
            "Washington Football Team": "WAS","New England Patriots": "NWE","Denver Broncos": "DEN","Jacksonville Jaguars": "JAX","Cincinnati Bengals": 
            "CIN","New York Giants": "NYG","New York Jets": "NYJ"}

def team_code(team_name, name_map=nfl_map):
    '''
    Retrieves the proper lookup code for the team searched for

    ::team_name Str:: location or name of team
    ::name_map Dict:: Dictionary mapping to lookup codes
    '''
    for team in name_map:
        if team_name.lower() in team.lower():
            return name_map[team]

def team_search(team_code):
    teams = Teams()
    return teams(team_code)

return_team = lambda team_name, name_map=nfl_map: team_search(team_code(team_name, name_map))

# simple function to replace Nones in list with 'Future game'
remove_none_games = lambda s: s if s is not None else 'Future game'

none_remove = lambda s: "---" if 'None' in s else s

date_split = lambda s: "/".join(s.split("-")[1:])
abbrs_changed = {'OTI': 'TEN', 'CLT': 'IND', 'CRD': 'ARI', 'RAM': 'LAR', 'SDG': 'LAC', 'HTX': 'HOU', 'NWE': 'NE', 'RAV': 'BAL', 'TAM': 'TB', 'RAI': 'LV'}
abbr_fix = lambda team: abbrs_changed[team] if team in abbrs_changed else team

def full_name(team, name_map=nfl_map):
    for t in nfl_map.keys():
        if team.lower() in t.lower():
            return t
    return team

def score_show(ours, theirs, loc):
    if loc == "Home":
        return f"{theirs}-{ours}"
    else:
        return f"{ours}-{theirs}"

def team_schedule(team_name, name_map=nfl_map):
    '''
    Returns formatted table showing a team's yearly schedule and wins/losses

    ::team_name Str:: Team to lookup
    ::name_map Dict:: Dictionary mapping to lookup codes
    '''
    try:
        schedule = team_search(team_code(team_name, name_map)).schedule.dataframe[['datetime', 'opponent_abbr', 'points_allowed', 'points_scored', 'result', 'location']]
        schedule = schedule.rename(columns={'datetime': 'Date', 'opponent_abbr': 'Vs.', 'result': 'Result'}).applymap(str)
        schedule['Score'] = schedule.apply(lambda df: score_show(df.points_scored, df.points_allowed, df.location), axis=1)
        schedule = schedule.drop(schedule[['points_scored', 'points_allowed']], axis=1)
        schedule['Result'] = schedule['Result'].map(none_remove).map(lambda s: s[0])
        schedule['Score'] = schedule['Score'].map(none_remove)
        schedule['Vs.'] = schedule['Vs.'].map(abbr_fix)
        schedule['Result'] = schedule[['Result', 'Score']].agg(' '.join, axis=1)
        schedule = schedule.drop(schedule[['Score', 'location']], axis=1)
        Date = schedule['Date'].str.split(" ", 1, True)
        schedule['Date'] = Date[0].map(date_split)
    except (AttributeError, HTTPError) as error:
        return "**Not a valid team**"
    return schedule

def gen_leaderboard(name_map=nfl_map, teams=[]):
    team_finder = Teams()
    if len(teams) > 0:
        try:
            teams = [team_finder(team_code(team, name_map)) for team in teams]
        except (AttributeError, HTTPError) as error:
            return "**Contains an incorrect team name dummy**"
    else:
        teams = team_finder
    teams = [team.dataframe[['abbreviation', 'rank', 'wins', 'losses']] for team in teams]
    leaderboard = pd.concat(teams).rename(columns={'abbreviation': 'Team', 'rank': 'Rank', 'wins': 'Wins', 'losses': 'Losses'}).applymap(str)
    leaderboard['Record'] = leaderboard[['Wins', 'Losses']].agg('-'.join, axis=1)
    leaderboard = leaderboard.drop(leaderboard[['Wins', 'Losses']], axis=1)
    leaderboard['Team'] = leaderboard['Team'].map(abbr_fix)
    return leaderboard

def split_df(df, row_limit=15):
    if df.shape[0] > row_limit:
        return [df[:row_limit]] + split_df(df[row_limit:])
    else:
        return [df]

l_dist = lambda l, n: sum([len(e) for e in l[:n]])

def find_next_break(l, max_size):
    for chunk in range(len(l)):
        if l_dist(l, chunk) > max_size:
            return chunk - 1
    return len(l)

def wrap(s):
    if s[:3] != '```':
        s = '```' + s
    if s[-3:] != '```':
        s += '```'
    return s

def split_cprint(s, max_length=1900):
    rows = s.split("\n")
    next_break = find_next_break(rows, max_length)
    if next_break == len(rows):
        return [wrap(s)]
    else:
        return [wrap("\n".join(rows[:next_break]))] + split_cprint("\n".join(rows[next_break:]))