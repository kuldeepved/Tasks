import os
import json
import random
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, quantiles
from collections import defaultdict

# Constants
N = 5000
M_RANGE = (50, 100)
K = [f"City_{i}" for i in range(1, random.randint(100, 200) + 1)]
NULL_PROBABILITY = (0.005, 0.001)  # 0.5% to 0.1%
OUTPUT_DIR = "/tmp/flights"

def random_flight_record():
    """Generating a random flight record"""
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "origin_city": random.choice(K),
        "destination_city": random.choice(K),
        "flight_duration_secs": random.randint(3600, 7200) if random.random() > random.uniform(*NULL_PROBABILITY) else None,
        "passengers_on_board": random.randint(50, 300) if random.random() > random.uniform(*NULL_PROBABILITY) else None,
    }

def generate_json_files():
    """Generating N JSON files with random flight data"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    for _ in range(N):
        origin_city = random.choice(K)
        folder = os.path.join(OUTPUT_DIR, datetime.now().strftime(f"%m-%y-{origin_city}"))
        Path(folder).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(folder, f"{origin_city}-flights.json")
        records = [random_flight_record() for _ in range(random.randint(*M_RANGE))]
        with open(file_path, "w") as file:
            json.dump(records, file)

def analyze_and_clean():
    start_time = time.time()
    total_records, dirty_records = 0, 0
    flight_durations = defaultdict(list)
    passenger_stats = defaultdict(lambda: {"arrived": 0, "left": 0})

    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                try:
                    flights = json.load(f)
                except json.JSONDecodeError:
                    continue
                total_records += len(flights)
                for flight in flights:
                    is_dirty = any(v is None for v in flight.values())
                    """Counting dirty records"""
                    if is_dirty:
                        dirty_records += 1
                        continue

                    # Collect stats for analysis
                    origin = flight["origin_city"]
                    destination = flight["destination_city"]
                    duration = flight["flight_duration_secs"]
                    passengers = flight["passengers_on_board"]

                    if duration is not None:
                        flight_durations[destination].append(duration)
                    if passengers is not None:
                        passenger_stats[origin]["left"] += passengers
                        passenger_stats[destination]["arrived"] += passengers

    # Analyze results
    top_destinations = sorted(flight_durations.items(), key=lambda x: len(x[1]), reverse=True)[:25]
    avg_and_p95 = {
        city: {
            "AVG": mean(durations),
            "P95": quantiles(durations, n=20)[18]  # 95th percentile is 19th element in 20-quantile
        }
        for city, durations in top_destinations
    }

    max_left_city = max(passenger_stats.items(), key=lambda x: x[1]["left"])
    max_arrived_city = max(passenger_stats.items(), key=lambda x: x[1]["arrived"])

    total_time = time.time() - start_time
    return {
        "total_records": total_records,
        "dirty_records": dirty_records,
        "total_run_duration": total_time,
        "avg_and_p95_top_25": avg_and_p95,
        "max_passengers_left": max_left_city,
        "max_passengers_arrived": max_arrived_city,
    }

if __name__ == "__main__":
    print("Generating JSON files...")
    generate_json_files()

    print("Analyzing and cleaning data...")
    results = analyze_and_clean()

    print("Results:")
    print(json.dumps(results, indent=4))
