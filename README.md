## Table of Contents  
- [Description](#Description)  
- [Installation](#Installation)
- [Usage](#Usage)  
- [Testing](#Testing)  
- [Datasets](#Datasets)  

<a name="Description"/>

# Carbon Aware Scheduler and ProvisionER (CASPER)

Using predictions of request during the next hour we calculate how the servers should be placed to handle
the requests while minimizing carbon and satsifying latency constraint.

Once servers are placed, the scheduler distributes the request between the regions such that carbon is minimized.

There are a few assumptions to consider for this implementation: 

1. The requests within a time-slot are treated as interchangeable.
2. The type of requests considered are short-lived, e.g. web requests.
3. Complete knowledge of incoming request rate for next time-slot, i.e. perfect predictions. 
4. Instantaneous communication between regions and the scheduler.
5. We ignore capacity planning, i.e. setting the maximum servers, capacities, etc such that all demand can be satisfied

<a name="Installation"/>

## Installation
Install all required packages specified in requirements.txt
```
pip install -r requirements.py
```
<a name="Usage"/>

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
                        Maximum latency allowed in milliseconds
  -m MAX_SERVERS, --max-servers MAX_SERVERS
                        Maximum pool of servers
  --rate RATE           Specify a constant rate
```

For **example** we could run this:
```
python -m scheduler -p "europe" -r 30 --latency 20 -t 48 --max-servers 15 --start-date 2021-10-22
```

In this respective order, we specify to run for the regions in europe [<sup id="a1">[1](#1)</sup>], schedule ever 30 minutes, where each request's round-trip must be under 20ms, for 48 hours, capping maximum server at one timestep to 15, with a starting date of 2021-10-22.  

<a name="Testing"/>

## Testing ![Test](https://github.com/Zonotora/umass/workflows/Test/badge.svg?branch=main&event=push)

To run all the tests `pytest` is required
```
pip install pytest
```

Run the following command in the root folder

```
pytest -v
```
<a name="Datasets"/>

## Datasets 

- _Latency_ uses [cloudping] [<sup id="a2">[2](#latency_cloudping)</sup>] containing inter-regional 50th percentile latency data for
AWS during one year. These are processed and applied in the code. 

- _Carbon Intensity_ uses [electricity map] [<sup id="a3">[3](#electricity_map)</sup>] for carbon metrics during decision making. We focus on the metric _average carbon intensity_ for regions.


<!-- THIS IS FOR HYPERLINKS -->
[cloudping]: https://www.cloudping.co/grid/latency/timeframe/1Y
[electricity map]: https://electricitymaps.com/


## Footnotes
[<a id="1">1</a>]
Only includes the 6 regions of where AWS is present. See [<sup id="a4">[4](#aws_regions)</sup>] for the whole list.
<b id="a1"></b> [↩](#a1)

## References
[<a id="2">2</a>] :
<a name="latency_cloudping"></a>
https://www.cloudping.co/grid/latency/timeframe/1Y
<b id="a1"></b> [↩](#a2)

<a id="electricity_map">[3]</a>
<a name="electricity_map"></a>
https://electricitymaps.com/
<b id="a1"></b> [↩](#a3)

<a id="4">[4]</a>
<a name="aws_regions"></a>
https://aws.amazon.com/about-aws/global-infrastructure/regions_az/
<b id="a1"></b> [↩](#a4)
