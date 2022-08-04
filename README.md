# Carbon Aware Scheduler and ProvisionER (CASPER)

Using predictions of request during the next hour we calculate how the servers should be placed to handle
the requests while minimizing carbon and satsifying latency constraint.

Once servers are placed, the scheduler distributes the request between the regions such that carbon is minimized.

There are a few assumptions to consider for this implementation: 

1. The properties of requests such as latency, load, and lifetime are uniform, hence requests are interchangeable
2. Requests considered are of type web requests. 
3. Complete knowledge of request rate for the incoming, i.e. perfect predictions. 
4. We can boot up servers in any region. 
5. We assume instantaneous communication between regions and the scheduler
6. We ignore capacity planning, i.e. setting the maximum servers, capacities, etc such that all demand can be satisfied


## Installation
Install all required packages specified in requirements.txt
```
pip install -r requirements.py
```

## Usage
To run the scheduler, make sure the working directory is the root folder of the repository and run the following

```
python -m scheduler --help
```

```
usage: __main__.py [-h] [-a {latency_greedy,carbon_greedy,carbon_aware}] [-t TIMESTEPS] [-r [0-60]] [--load LOAD] [--save] [-d START_DATE] [-v] [-l LATENCY] [-m MAX_SERVERS]
                   [--rate RATE]

optional arguments:
  -h, --help            show this help message and exit
  -a {latency_greedy,carbon_greedy,carbon_aware}, --algorithm {latency_greedy,carbon_greedy,carbon_aware}
                        The scheduling algorithm to use
  -t TIMESTEPS, --timesteps TIMESTEPS
                        The total number of hours
  -r [0-60], --request-update-interval [0-60]
                        The number of minutes between each scheduling
  --load LOAD           Name of file to load and plot
  --save                Name of file to save
  -d START_DATE, --start-date START_DATE
                        Start date in ISO format (YYYY-MM-DD)
  -v, --verbose         Print information for every timestep
  -l LATENCY, --latency LATENCY
                        Maximum latency allowed
  -m MAX_SERVERS, --max-servers MAX_SERVERS
                        Maximum pool of servers
  --rate RATE           Specify a constant rate
```

## Testing ![Test](https://github.com/Zonotora/umass/workflows/Test/badge.svg?branch=main&event=push)

To run all the tests `pytest` is required
```
pip install pytest
```

Run the following command in the root folder

```
pytest -v
```

## Datasets 

For latency we use [cloudping] containing average latency to AWS during one year for implemented regions. These are applied manually in the code. 

[cloudping]: https://www.cloudping.co/grid/latency/timeframe/1Y
