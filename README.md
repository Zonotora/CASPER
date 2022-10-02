## Table of Contents
- [Carbon Aware Scheduler and ProvisionER (CASPER)](#carbon-aware-scheduler-and-provisioner-casper)
- [Installation](#installation)
- [Usage](#usage)
- [Datasets](#datasets)
- [References](#references)

# Carbon Aware Scheduler and ProvisionER (CASPER)

Using predictions of request during the next hour we calculate how the servers should be placed to handle
the requests while minimizing carbon and satsifying latency constraint.

Once servers are placed, the scheduler distributes the request between the regions such that carbon is minimized.

## Idea and Overview
Space is divided into regions. Each region have attributes such as
- Carbon intensity trace $I(t)$
- Outgoing request rate $\lambda(t)$
- Maximum tolerated latency $L$

We are looking at the problem of scheduling those outgoing requests to regions
where $I(t)$ is relatively small while satisfying many constraints, see optimization problem.
We call this part the Carbon Aware Scheduler (CAS). We also have another part that shift compute units between
the regions to allow for even more carbon savings. We call this the Carbon Aware Provisioner (CAP).

The high-level architecture of the CAS is illustrated in the following diagram which can be read from left to right.
I.e. each region's outgoing requests are proxied through the "scheduler" which decides what region to send the request to.

![diagram](https://user-images.githubusercontent.com/43207511/184157966-3a8c8033-b34c-49cf-bc98-338ea4a8106f.png)

The scheduler is implemented in `scheduler/milp_scheduler.py`.


A more zoomed in version of when the requests coming from the scheduer goes into a region $R_i$ that contain $m_i$ different servers is shown below.

![server_manager](https://user-images.githubusercontent.com/43207511/184157845-fa24d2b0-3ce4-4906-83ce-ac2ba9b8d462.png)

The `ServerManager` resides in `scheduler/server.py`.

## Workflow diagram

A few colors to signal configurations or states
- ![#D5E8D4](https://via.placeholder.com/15/D5E8D4/D5E8D4.png) `Start of simulation`
- ![#DAE8FC](https://via.placeholder.com/15/DAE8FC/DAE8FC.png) `Basic steps for simulation`
- ![#FFF2CC](https://via.placeholder.com/15/FFF2CC/FFF2CC.png) `True/False condition`
- ![#E1D5E7](https://via.placeholder.com/15/E1D5E7/E1D5E7.png) `Type: carbon greedy`
- ![#B0E3E6](https://via.placeholder.com/15/B0E3E6/B0E3E6.png) `Type: latency greedy`
- ![#F8CECC](https://via.placeholder.com/15/F8CECC/F8CECC.png) `End of simulation`

<img src="https://github.com/umassos/casper/blob/main/images/Workflow-Diagram.jpg" width="500">

### Assumptions and limitations

With this implementation there are a few assumptions to consider:

1. The requests within a time-slot are treated as interchangeable.
2. The type of requests considered are short-lived, e.g. web requests.
3. Complete knowledge of incoming request rate for next time-slot, i.e. perfect predictions.
4. Instantaneous communication between regions and the scheduler.
5. We ignore capacity planning, i.e. setting the maximum servers, capacities, etc such that all demand can be satisfied

# Installation
Install all required packages specified in requirements.txt
```
pip install -r requirements.py
```

# Usage

To run the scheduler, make sure the working directory is the root folder of the repository. To display the help menu, run the following

```
python -m casper --help
```

```
usage: __main__.py [-h] [-t TIMESTEPS] [-u [0-60]] [-r REQUEST_RATE] [--save] [-d START_DATE] [--max-latency MAX_LATENCY] [--max-servers MAX_SERVERS] [--server-capacity SERVER_CAPACITY] [--region {na,eu}]
                   [--scheduler {carbon,latency}] [--replay] [-v] [--verbose-milp]

options:
  -h, --help            show this help message and exit
  -t TIMESTEPS, --timesteps TIMESTEPS
                        The total number of hours
  -u [0-60], --request-update-interval [0-60]
                        The number of minutes between each scheduling
  -r REQUEST_RATE, --request-rate REQUEST_RATE
                        Specify a constant request rate per hour
  --save                Save file to /saved with the following format YYYY-MM-DD_hh:mm:ss
  -d START_DATE, --start-date START_DATE
                        Start date in ISO format (YYYY-MM-DD)
  --max-latency MAX_LATENCY
                        Maximum latency allowed
  --max-servers MAX_SERVERS
                        Maximum pool of servers
  --server-capacity SERVER_CAPACITY
                        The capacity of each server
  --region {na,eu}      The region we want to load our data from
  --scheduler {carbon,latency}
                        Define what you wish to minimize: carbon/latency
  --replay              Use akamai dataset instead of MILP scheduler to produce output
  -v, --verbose         Print information for every timestep
  --verbose-milp        Print the log from the MILP scheduler
```

For **example** we could run this:
```
python -m casper --region na -u 30 -t 48 --max-latency 200 --max-servers 150 --start-date 2022-08-05
```

In this respective order, we specify to run for the regions in north america, schedule ever 30 minutes, where each request's round-trip must be below 200ms, for 48 hours, capping maximum servers within one hour to 150, with a starting date of 2022-08-05.

# Datasets
```
data
└── <region>
    ├── carbon_intensity.csv
    ├── incoming.csv
    ├── latency.csv
    ├── offset.csv
    └── request.csv
```

- _Latency_ uses [cloudping] [<sup id="a2">[2](#latency_cloudping)</sup>] containing inter-regional 50th percentile latency data for
AWS during one year. These are processed and applied in the code.

- _Carbon Intensity_ uses [electricity map] [<sup id="a3">[3](#electricity_map)</sup>] for carbon metrics during decision making. We focus on the metric _average carbon intensity_ for regions.



<!-- THIS IS FOR HYPERLINKS -->
[cloudping]: https://www.cloudping.co/grid/latency/timeframe/1Y
[electricity map]: https://electricitymaps.com/

# References
<a name="latency_cloudping"></a>
[1] https://www.cloudping.co/grid/latency/timeframe/1Y

<a name="electricity_map"></a>
[2] https://electricitymaps.com/

<a name="aws_regions"></a>
[3] https://aws.amazon.com/about-aws/global-infrastructure/regions_az/
