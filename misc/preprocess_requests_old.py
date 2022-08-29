from datetime import datetime, timezone

print("datetime,timestamp,requests")
with open("data/de.out") as f:
    lines = f.readlines()
    for line in lines:
        [date, timestamp, requests] = line.split()
        timestamp = int(float(timestamp))
        requests = int(requests)
        if timestamp & 1 == 1:
            timestamp -= 1
        elif timestamp & 9 == 9:
            timestamp += 1

        date = datetime.fromtimestamp(timestamp).replace(tzinfo=timezone.utc)
        if date.year != 2011:
            continue
        date = date.replace(year=2021)
        timestamp = int(date.timestamp())
        print(f"{date},{timestamp},{requests}")
