from bs4 import BeautifulSoup
import time
import urllib2
import json
import numpy as np
import pandas as pd

# Create a soup out of the manually downloaded html code
soup = BeautifulSoup(open("federer.htm"), 'html.parser')

# Get all tournaments
tourneys = soup.find_all(class_="activity-tournament-table")

# Used to make unique match IDs
def match_hash(i,j):
    return .5*(i + j)*(i + j + 1) + j

match_overview = []
roger_stats = []
opponent_stats = []
for i in xrange(len(tourneys)):
    # parse the dates of the tournament
    date = tourneys[i].find(class_="tourney-dates").text.encode("utf8").strip()

    # parse a list of matches in the tournament
    matches = tourneys[i].find(class_="mega-table").find_all(class_="day-table-name")
    for j in xrange(len(matches)):
        # This is the timeout I found was necessary to not fail.
        time.sleep(np.random.uniform(low=5, high=8))

        try:
            m = matches[j]
            m_hash = match_hash(i,j)

            # parse the name of the opponent
            opponent = m.text.strip()
            if opponent == "Bye":
                print "Bye found"
                continue
                
            # parse the rank of the opponent
            rank = int(m.parent.previous_sibling.previous_sibling.text.strip())
            
            # parse the round of the tournament in which the match was played
            tourney_round = m.parent.previous_sibling.previous_sibling.previous_sibling.previous_sibling.text.strip()
            # record the result W/L
            result = m.parent.next_sibling.next_sibling
            result_text = result.text.strip()
            
            # record the score of the match
            score = result.next_sibling.next_sibling
            score_text = score.text.strip()
            
            # store the url that links to the full match stats
            match_stats_url = score.a['href']
            
            # create a new soup for the new webpage
            stats = BeautifulSoup(urllib2.urlopen(match_stats_url).read(), 'html.parser')

            # load the appropriate JSON object that houses all the data
            match_stats = json.loads(stats.find('script', id="matchStatsData", type="text/javascript").text)[0]
            
            # store all the high-level statistics and information
            match_overview.append([m_hash, date, opponent, rank, tourney_round, result_text, score_text])

            # store Roger's stats
            r = pd.DataFrame(match_stats["playerStats"], index=[m_hash])
            roger_stats.append(r.values.flatten().tolist())
            
            # store opponent's stats
            o = pd.DataFrame(match_stats["opponentStats"], index=[m_hash])
            opponent_stats.append(o.values.flatten().tolist())
        except:
            print i,j,"Failed"
            
    print i+1, "/", len(tourneys)


# Do a little bit of cleaning to the resulting DataFrames
match_overview = pd.DataFrame(match_overview, columns=["MatchID", "TourneyDate", "Opp", "Rank", "Round", "Result", "Score"])
match_overview.MatchID = match_overview.MatchID.astype(int)
roger = pd.DataFrame(roger_stats, columns=r.columns)
roger["MatchID"] = match_overview.MatchID
roger = roger[[roger.columns[-1]] + roger.columns[:-1].tolist()]
opponent = pd.DataFrame(opponent_stats, columns=o.columns)
opponent["MatchID"] = match_overview.MatchID
opponent = opponent[[opponent.columns[-1]] + opponent.columns[:-1].tolist()]

# Store the DataFrames as pickle files.
match_overview.to_pickle("match_overview.pkl")
roger.to_pickle("roger.pkl")
opponent.to_pickle("opponent.pkl")
