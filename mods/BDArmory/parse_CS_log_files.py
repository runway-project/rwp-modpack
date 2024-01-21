#!/usr/bin/env python3

# Standard library imports
import argparse
import re
import sys
from pathlib import Path

VERSION = "3.0"

parser = argparse.ArgumentParser(description="Log file parser for continuous spawning logs.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("logs", nargs='*', help="Log files to parse. If none are given, the latest log file is parsed.")
parser.add_argument("-n", "--no-file", action='store_true', help="Don't create a csv file.")
parser.add_argument("-w", "--weights", type=str, default="3,1.5,-1,4e-3,1e-4,4e-5,0.035,6e-4,1.5e-4, 5e-5,0.15,2e-3,3e-5,1.5e-5,0.075,0,0", help="Score weights.")
parser.add_argument("--show-weights", action='store_true', help="Show the score weights.")
parser.add_argument("-s", "--separately", action='store_true', help="Show the results of each log separately (for multiple logs).")
parser.add_argument("--version", action='store_true', help="Show the script version, then exit.")
args = parser.parse_args()

if args.version:
    print(f"Version: {VERSION}")
    sys.exit()

log_dir = Path(__file__).parent / "Logs" if len(args.logs) == 0 else Path('.')

fields = ["kills", "assists", "deaths", "hits", "bullet damage", "bullet damage taken", "rocket strikes", "rocket parts hit", "rocket damage",
    "rocket damage taken", "missile strikes", "missile parts hit", "missile damage", "missile damage taken", "rammed parts", "accuracy", "rocket accuracy"]
fields_short = {field: field_short for field, field_short in zip(fields, ["Kills", "Assists", "Deaths", "Hits", "Damage", "DmgTkn", "RktHits", "RktParts", "RktDmg", "RktDmgTkn", "MisHits", "MisParts", "MisDmg", "MisDmgTkn", "Ram", "Acc%", "RktAcc%"])}
try:
    weights = {field: float(w) for field, w in zip(fields, args.weights.split(','))}
    if len(weights) != len(fields):
        raise ValueError("Invalid number of weights.")
except:
    raise ValueError("Failed to parse input weights")

if args.show_weights:
    field_width = max(len(f) for f in fields)
    for f, w in weights.items():
        print(f"{f}:{' '*(field_width - len(f))} {w}")
    sys.exit()

if len(args.logs) > 0:
    competition_files = [Path(filename) for filename in args.logs if filename.endswith(".log")]
else:
    competition_files = list(sorted(list(log_dir.glob("cts-*.log"))))
    if len(competition_files) > 0:
        competition_files = competition_files[-1:]

data = {}
for filename in competition_files:
    with open(log_dir / filename if len(args.logs) == 0 else filename, "r") as file_data:
        data[filename.name] = {}
        Craft_Name = None
        for line in file_data:
            if not "BDArmory.VesselSpawner" in line:  # Identifier for continuous spawn logs.
                continue
            if " Name:" in line:  # Next craft
                Craft_Name = line.split(" Name:")[-1].replace("\n", "")
                data[filename.name][Craft_Name] = {"kills": 0, "assists": 0, "deaths": 0, "hits": 0, "bullet damage": 0, "acc hits": 0, "shots": 0, "accuracy": 0, "rocket strikes": 0, "rocket parts hit": 0,
                    "rocket damage": 0, "acc rocket strikes": 0, "rockets fired": 0, "rocket accuracy": 0, "missile strikes": 0, "missile parts hit": 0, "missile damage": 0, "score": 0, "damage/spawn": 0}
            elif " DEATHCOUNT:" in line:  # Counts up deaths
                data[filename.name][Craft_Name]["deaths"] = int(line.split("DEATHCOUNT:")[-1].replace("\n", ""))
            elif (m := re.match(".*CLEAN[^:]*:", line)) is not None:  # Counts up clean kills, frags, explodes and rams
                killedby = {int(nr): killer for nr, killer in (cleanKill.split(":") for cleanKill in m.string[m.end():].replace("\n", "").split(", "))}
                if "killed by" in data[filename.name][Craft_Name]:
                    data[filename.name][Craft_Name]["killed by"].update(killedby)
                else:
                    data[filename.name][Craft_Name]["killed by"] = killedby  # {death_nr: killer}
            elif " GMKILL:" in line:  # GM kills
                data[filename.name][Craft_Name]["GM kills"] = {int(nr): killer for nr, killer in (gmKill.split(":") for gmKill in line.split(":  GMKILL:")[-1].replace("\n", "").split(", ")) if killer != "LandedTooLong"}
            elif " WHOSHOTME:" in line:  # Counts up hits
                data[filename.name][Craft_Name]["shot by"] = {int(life): {by: int(hits) for hits, by in (entry.split(":", 1) for entry in hitsby.split(";"))}
                                                                  for life, hitsby in (entry.split(":", 1) for entry in line.split(":  WHOSHOTME:")[-1].replace("\n", "").split(", "))}
            elif " WHOSTRUCKMEWITHROCKETS:" in line:  # Counts up hits
                data[filename.name][Craft_Name]["rocket strike by"] = {int(life): {by: int(hits) for hits, by in (entry.split(":", 1) for entry in hitsby.split(";"))}
                                                                           for life, hitsby in (entry.split(":", 1) for entry in line.split(":  WHOSTRUCKMEWITHROCKETS:")[-1].replace("\n", "").split(", "))}
            elif " WHOSTRUCKMEWITHMISSILES:" in line:  # Counts up hits
                data[filename.name][Craft_Name]["missile strike by"] = {int(life): {by: int(hits) for hits, by in (entry.split(":", 1) for entry in hitsby.split(";"))}
                                                                            for life, hitsby in (entry.split(":", 1) for entry in line.split(":  WHOSTRUCKMEWITHMISSILES:")[-1].replace("\n", "").split(", "))}
            elif " WHOPARTSHITMEWITHROCKETS:" in line:  # Counts up parts hit
                data[filename.name][Craft_Name]["rocket parts hit by"] = {int(life): {by: int(parts) for parts, by in (entry.split(":", 1) for entry in partshitby.split(";"))}
                                                                              for life, partshitby in (entry.split(":", 1) for entry in line.split(":  WHOPARTSHITMEWITHROCKETS:")[-1].replace("\n", "").split(", "))}
            elif " WHOPARTSHITMEWITHMISSILES:" in line:  # Counts up parts hit
                data[filename.name][Craft_Name]["missile parts hit by"] = {int(life): {by: int(parts) for parts, by in (entry.split(":", 1) for entry in partshitby.split(";"))}
                                                                               for life, partshitby in (entry.split(":", 1) for entry in line.split(":  WHOPARTSHITMEWITHMISSILES:")[-1].replace("\n", "").split(", "))}
            elif " WHODAMAGEDMEWITHBULLETS:" in line:  # Counts up damage
                data[filename.name][Craft_Name]["bullet damage by"] = {int(life): {by: float(damage) for damage, by in (entry.split(":", 1) for entry in damageby.split(";"))}
                                                                           for life, damageby in (entry.split(":", 1) for entry in line.split(":  WHODAMAGEDMEWITHBULLETS:")[-1].replace("\n", "").split(", "))}
            elif " WHODAMAGEDMEWITHROCKETS:" in line:  # Counts up damage
                data[filename.name][Craft_Name]["rocket damage by"] = {int(life): {by: float(damage) for damage, by in (entry.split(":", 1) for entry in damageby.split(";"))}
                                                                           for life, damageby in (entry.split(":", 1) for entry in line.split(":  WHODAMAGEDMEWITHROCKETS:")[-1].replace("\n", "").split(", "))}
            elif " WHODAMAGEDMEWITHMISSILES:" in line:  # Counts up damage
                data[filename.name][Craft_Name]["missile damage by"] = {int(life): {by: float(damage) for damage, by in (entry.split(":", 1) for entry in damageby.split(";"))}
                                                                            for life, damageby in (entry.split(":", 1) for entry in line.split(":  WHODAMAGEDMEWITHMISSILES:")[-1].replace("\n", "").split(", "))}
            elif " WHORAMMEDME:" in line:  # Counts up rams
                data[filename.name][Craft_Name]["rammed by"] = {int(life): {by: int(parts) for parts, by in (entry.split(":", 1) for entry in partshitby.split(";"))}
                                                                    for life, partshitby in (entry.split(":", 1) for entry in line.split(":  WHORAMMEDME:")[-1].replace("\n", "").split(", "))}
            elif " ACCURACY:" in line:
                for item in line.split(" ACCURACY:")[-1].replace("\n", "").split(","):
                    _, hits, shots, rocketStrikes, rocketsFired = re.split('[:/]', item)
                    data[filename.name][Craft_Name]["acc hits"] += int(hits)
                    data[filename.name][Craft_Name]["shots"] += int(shots)
                    data[filename.name][Craft_Name]["acc rocket strikes"] += int(rocketStrikes)
                    data[filename.name][Craft_Name]["rockets fired"] += int(rocketsFired)
                data[filename.name][Craft_Name]["accuracy"] = 100 * data[filename.name][Craft_Name]["acc hits"] / data[filename.name][Craft_Name]["shots"] if data[filename.name][Craft_Name]["shots"] > 0 else 0
                data[filename.name][Craft_Name]["rocket accuracy"] = 100 * data[filename.name][Craft_Name]["acc rocket strikes"] / data[filename.name][Craft_Name]["rockets fired"] if data[filename.name][Craft_Name]["rockets fired"] > 0 else 0

        for Craft_Name in data[filename.name]:
            data[filename.name][Craft_Name]["hits"] = sum(hitby[life][Craft_Name] for hitby in (data[filename.name][other]["shot by"] for other in data[filename.name]
                                                          if other != Craft_Name and "shot by" in data[filename.name][other]) for life in hitby if Craft_Name in hitby[life])
            data[filename.name][Craft_Name]["rocket strikes"] = sum(hitby[life][Craft_Name] for hitby in (data[filename.name][other]["rocket strike by"] for other in data[filename.name]
                                                                    if other != Craft_Name and "rocket strike by" in data[filename.name][other]) for life in hitby if Craft_Name in hitby[life])
            data[filename.name][Craft_Name]["missile strikes"] = sum(hitby[life][Craft_Name] for hitby in (data[filename.name][other]["missile strike by"] for other in data[filename.name]
                                                                     if other != Craft_Name and "missile strike by" in data[filename.name][other]) for life in hitby if Craft_Name in hitby[life])

            data[filename.name][Craft_Name]["rocket parts hit"] = sum(partshitby[life][Craft_Name] for partshitby in (data[filename.name][other]["rocket parts hit by"] for other in data[filename.name]
                                                                      if other != Craft_Name and "rocket parts hit by" in data[filename.name][other]) for life in partshitby if Craft_Name in partshitby[life])
            data[filename.name][Craft_Name]["missile parts hit"] = sum(partshitby[life][Craft_Name] for partshitby in (data[filename.name][other]["missile parts hit by"]
                                                                       for other in data[filename.name] if other != Craft_Name and "missile parts hit by" in data[filename.name][other]) for life in partshitby if Craft_Name in partshitby[life])

            data[filename.name][Craft_Name]["bullet damage"] = sum(damageby[life][Craft_Name] for damageby in (data[filename.name][other]["bullet damage by"] for other in data[filename.name]
                                                                   if other != Craft_Name and "bullet damage by" in data[filename.name][other]) for life in damageby if Craft_Name in damageby[life])
            data[filename.name][Craft_Name]["rocket damage"] = sum(damageby[life][Craft_Name] for damageby in (data[filename.name][other]["rocket damage by"] for other in data[filename.name]
                                                                   if other != Craft_Name and "rocket damage by" in data[filename.name][other]) for life in damageby if Craft_Name in damageby[life])
            data[filename.name][Craft_Name]["missile damage"] = sum(damageby[life][Craft_Name] for damageby in (data[filename.name][other]["missile damage by"] for other in data[filename.name]
                                                                    if other != Craft_Name and "missile damage by" in data[filename.name][other]) for life in damageby if Craft_Name in damageby[life])

            data[filename.name][Craft_Name]["bullet damage taken"] = sum(damage for damageby in data[filename.name][Craft_Name]['bullet damage by'].values() for damage in damageby.values()) if 'bullet damage by' in data[filename.name][Craft_Name] else 0
            data[filename.name][Craft_Name]["rocket damage taken"] = sum(damage for damageby in data[filename.name][Craft_Name]['rocket damage by'].values() for damage in damageby.values()) if 'rocket damage by' in data[filename.name][Craft_Name] else 0
            data[filename.name][Craft_Name]["missile damage taken"] = sum(damage for damageby in data[filename.name][Craft_Name]['missile damage by'].values()
                                                                          for damage in damageby.values()) if 'missile damage by' in data[filename.name][Craft_Name] else 0

            data[filename.name][Craft_Name]["rammed parts"] = sum(partshitby[life][Craft_Name] for partshitby in (data[filename.name][other]["rammed by"] for other in data[filename.name]
                                                                  if other != Craft_Name and "rammed by" in data[filename.name][other]) for life in partshitby if Craft_Name in partshitby[life])

            data[filename.name][Craft_Name]["damage/spawn"] = (data[filename.name][Craft_Name]["bullet damage"] + data[filename.name][Craft_Name]["rocket damage"] +
                                                               data[filename.name][Craft_Name]["missile damage"]) / (1 + data[filename.name][Craft_Name]["deaths"])

            data[filename.name][Craft_Name]["kills"] = sum(1 for kill in (data[filename.name][other]["killed by"] for other in data[filename.name] if other !=
                                                           Craft_Name and "killed by" in data[filename.name][other]) for life in kill if Craft_Name == kill[life])

            # Aggregate the damagers for computing assists later.
            data[filename.name][Craft_Name]['damaged by'] = {}
            if 'bullet damage by' in data[filename.name][Craft_Name]:
                data[filename.name][Craft_Name]['damaged by'] = {k: set(v) for k, v in data[filename.name][Craft_Name]['bullet damage by'].items() if k < data[filename.name][Craft_Name]['deaths']}
            if 'rocket damage by' in data[filename.name][Craft_Name]:
                for k, v in data[filename.name][Craft_Name]['rocket damage by'].items():
                    if k < data[filename.name][Craft_Name]['deaths']:
                        if k in data[filename.name][Craft_Name]['damaged by']:
                            data[filename.name][Craft_Name]['damaged by'][k] = data[filename.name][Craft_Name]['damaged by'][k].union(set(v))
                        else:
                            data[filename.name][Craft_Name]['damaged by'][k] = set(v)
            if 'missile damage by' in data[filename.name][Craft_Name]:
                for k, v in data[filename.name][Craft_Name]['missile damage by'].items():
                    if k < data[filename.name][Craft_Name]['deaths']:
                        if k in data[filename.name][Craft_Name]['damaged by']:
                            data[filename.name][Craft_Name]['damaged by'][k] = data[filename.name][Craft_Name]['damaged by'][k].union(set(v))
                        else:
                            data[filename.name][Craft_Name]['damaged by'][k] = set(v)
            if 'rammed by' in data[filename.name][Craft_Name]:
                for k, v in data[filename.name][Craft_Name]['rammed by'].items():
                    if k < data[filename.name][Craft_Name]['deaths']:
                        if k in data[filename.name][Craft_Name]['damaged by']:
                            data[filename.name][Craft_Name]['damaged by'][k] = data[filename.name][Craft_Name]['damaged by'][k].union(set(v))
                        else:
                            data[filename.name][Craft_Name]['damaged by'][k] = set(v)

            # Sanity check
            if data[filename.name][Craft_Name]["hits"] != data[filename.name][Craft_Name]["acc hits"]:
                print(f"Warning: inconsistency in hit counting {data[filename.name][Craft_Name]['hits']} vs {data[filename.name][Craft_Name]['acc hits']} for log {filename.name}")
            if data[filename.name][Craft_Name]["rocket strikes"] != data[filename.name][Craft_Name]["acc rocket strikes"]:
                print(f"Warning: inconsistency in rocket strike counting {data[filename.name][Craft_Name]['rocket strikes']} vs {data[filename.name][Craft_Name]['acc rocket strikes']} for log {filename.name}")

        # Compute assists and scores.
        for Craft_Name in data[filename.name]:
            data[filename.name][Craft_Name]["assists"] = sum(1 for other in data[filename.name] for life, damagedby in data[filename.name][other]['damaged by'].items() if Craft_Name in damagedby and not (
                'killed by' in data[filename.name][other] and life in data[filename.name][other]['killed by']) and not ('GM kills' in data[filename.name][other] and life in data[filename.name][other]['GM kills']))

            data[filename.name][Craft_Name]["score"] = sum(weights[field] * data[filename.name][Craft_Name][field] for field in fields)

if len(data) > 0:
    # Write results to console
    if args.separately:
        for filename, summary in data.items():
            print(f"Results for {filename}:")
            name_length = max([len(craft) for craft in summary])
            field_lengths = {field: max(len(fields_short[field]) + 2, 8) for field in fields}
            print(f"Name{' '*(name_length-4)}     score" + "".join(f"{fields_short[field]:>{field_lengths[field]}}" for field in fields))
            for craft in sorted(summary, key=lambda c: summary[c]["score"], reverse=True):
                print(f"{craft}{' '*(name_length-len(craft))}  {summary[craft]['score']:8.2f}" +
                      "".join(f"{summary[craft][field]:>{field_lengths[field]}.0f}" if 'accuracy' not in field else f"{summary[craft][field]:>{field_lengths[field]-1}.1f}%" for field in fields))
            print("")

            if not args.no_file:
                # Write results to file
                with open(log_dir / f"results-{Path(filename).stem}.csv", "w") as results_data:
                    results_data.write("Name,Score," + ",".join(fields) + "\n")
                    for craft in sorted(summary, key=lambda c: summary[c]["score"], reverse=True):
                        results_data.write(f"{craft},{summary[craft]['score']:.2f}," + ",".join(f"{summary[craft][field]:.2f}" for field in fields) + "\n")
    else:
        # Merge the results from each log into a single summary.
        summary = {}
        for filename, entry in data.items():
            for craft, results in entry.items():
                if craft not in summary:
                    summary[craft] = {f: results[f] for f in fields + ['acc hits', 'shots', 'acc rocket strikes', 'rockets fired', 'score']}
                else:
                    for f in fields + ['acc hits', 'shots', 'acc rocket strikes', 'rockets fired', 'score']:
                        summary[craft][f] = summary[craft].get(f, 0) + results[f]
        for craft, entry in summary.items():
            entry['accuracy'] = entry['hits'] / entry['shots'] * 100 if entry['shots'] > 0 else 0
            entry['rocket accuracy'] = entry['rocket strikes'] / entry['rockets fired'] * 100 if entry['rockets fired'] > 0 else 0

        name_length = max([len(craft) for craft in summary])
        field_lengths = {field: max(len(fields_short[field]) + 2, 8) for field in fields}
        print(f"Name{' '*(name_length-4)}     score" + "".join(f"{fields_short[field]:>{field_lengths[field]}}" for field in fields))
        for craft in sorted(summary, key=lambda c: summary[c]["score"], reverse=True):
            print(f"{craft}{' '*(name_length-len(craft))}  {summary[craft]['score']:8.2f}" +
                  "".join(f"{summary[craft][field]:>{field_lengths[field]}.0f}" if 'accuracy' not in field else f"{summary[craft][field]:>{field_lengths[field]-1}.1f}%" for field in fields))

        if not args.no_file:
            # Write results to file
            with open(log_dir / f"results.csv", "w") as results_data:
                results_data.write("Name,Score," + ",".join(fields) + "\n")
                for craft in sorted(summary, key=lambda c: summary[c]["score"], reverse=True):
                    results_data.write(f"{craft},{summary[craft]['score']:.2f}," + ",".join(f"{summary[craft][field]:.2f}" for field in fields) + "\n")
else:
    print(f"No valid log files found.")
