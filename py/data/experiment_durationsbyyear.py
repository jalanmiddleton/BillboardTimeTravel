import csv

import datetime
import statistics
import sys
from pathlib import Path
from pprint import pprint
sys.path.append(str(Path(__file__).parent.parent))

scores_csv = "./py/data/top40score.csv"
uris_csv = "./py/data/songlinks.csv"
debuts_csv = "./py/data/songdebuts.csv"
year_adjustment_csv = "./py/data/yearadjuster.csv"

scores = {}
with open(scores_csv, "r") as infile:
    reader = csv.reader(infile)
    next(reader)
    for *title_artist, weeks_in_top_40 in reader:
        scores[tuple(title_artist)] = int(weeks_in_top_40)

debuts = {}
with open(debuts_csv, "r") as infile:
    reader = csv.reader(infile)
    next(reader)
    for *title_artist, debut in reader:
        debuts[tuple(title_artist)] = datetime.date.fromisoformat(debut).year

years = {}
for title_artist, debut in debuts.items():
    if debut not in years:
        years[debut] = []
    if title_artist in scores:
        years[debut].append([*title_artist, scores[title_artist]])

aggregate_scores = []
year_scores = {}
for year in years:
    years[year] = sorted(years[year], key=lambda title_artist_score: title_artist_score[2], reverse=True)
    top40scores = [score for *_, score in years[year][:40]]
    year_scores[year] = top40scores
    aggregate_scores.extend(top40scores)
    print(f'{year}: {str(top40scores[:10])} -> (Mean: {statistics.mean(top40scores)}, Median: {statistics.median(top40scores)})')

agg_median = statistics.median(aggregate_scores)
print(f'All -> (Mean: {statistics.mean(aggregate_scores)}, Median: {agg_median})')
with open(year_adjustment_csv, "w", newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(['year', 'coeff'])
    for year in year_scores:
        top40scores = year_scores[year]
        adjuster = agg_median / statistics.median(top40scores)
        writer.writerow([year, round(adjuster, 2)])
        top40scores = [round(adjuster * x, 2) for x in top40scores]
        print(f'{year}: {str(top40scores[:10])} -> (Mean: {statistics.mean(top40scores)}, Median: {statistics.median(top40scores)})')
