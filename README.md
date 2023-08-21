## Short Description of implementation, for context
Our application is a wireless vehicular network implementation (i.e. drones). This application is run on a Pi through the `master_process.py` file. This file will create a number of `drone.py` subprocesses, which each have their own coordinates as the move around our coordinate plane. `master_process.py` is used to carry out the following tasks:
* keep track of the coordinates of each drone subprocess
* determine if two drones are are within a certain range of each other in the coordinate plane, and if they are, they are considered to be wirelessly connected (and are allowed to communicate with each other, advertise their data with each other, etc.)
* communicate these drone coordinates with other Pis, so that drone subprocesses can communicate across Pis.

Therefore, `master_process.py` does not represent anything in either a real-world network topology (i.e., it is not a centralized node, router, etc.), it is not a device in our network (our devices are the drone subprocesses), nor does it represent anything in our NDN implementation. It is simply a way for us to launch our drones, know the coordinates of our drones, and determine if two drones are close enough to wirelessly connect to each other, in an abstract way. This allows for the network routes to constantly change throughout a run of the application, as drones move around freely and connect/disconnect with other drones.

## Command line arguments
To run `master_process.py`, we have the following command line arguments:
* `-c` or `--count`: Number of drones to be launched (recommended to run 5+)
* `-r` or `--drone_range`: The wireless range of the drones on the coordinate plane 
* `-a` or `--area_dimensions`: The max X and Y values on the coordinate plane
* `-i` or `--host`: IP address of *this* Pi, e.g. 10.35.70.20 for Pi 20
* `-p` or `--port`: Port for `master_process.py` (will be incremented until one found that is available), and also the base number used for finding unique (available) ports for each drone
* `-o` or `--other_pis`: If other instances of `master_process.py` are currently running on other Pis, then this newly launched version of `master_process.py` needs to share the coordinate data for its drones with them. The other Pis IP:PORT must be passed as a set (in string form): `"{ '10.35.70.20:33400', '10.35.70.21:33400' }"`.
* `-f` or `--outfile`: The output file for `master_process.py`, should be unique for every instance of `master_process.py` currently running (recommended names: `out1`, `out2`, etc.)
* `-l` or `--location`: This is the name of the file in `/data_to_use` to use for sensor data (omit the `.csv` file extension). It is also used in the namespace of the data, i.e. `/52.953,-6.461/temperature/08`. If running on different Pis, you can use different files here (i.e. 2 Pis are using `52.953,-6.461`, while 1 is using `53.291,-6.461`). These are equivalent to the `/Cork`, `/Dublin`, etc namespaces/locations mentioned in the report/presentation, and the FIB handles them equivalently to how these were described in the report. This defaults to `"52.953,-6.461"` if no arugment passed.

## Launching the application
E.g. on Pi 20:
`python3 master_process.py -c 5 -r 8 -a 10 -i 10.35.70.20 -f out`

This file can run in isolation. You can see the output of each individual Drone in the `/drone_output` folder (best to view these while the application is still running, and ignore any files that start with `1_`). When you are finished running this application, press `Ctrl + C` then run `killall python3` (you will likely see some broken pipe errors, this is fine and is just a result of the processes closing).

While the above file is running on Pi 20, you can run the following on Pi 21, which will add more drones to the network:
`python3 master_process.py -c 5 -r 8 -a 10 -i 10.35.70.21 -o "{ '10.35.70.20:33400' }" -f out2`

**NOTE**: If Pi 20's `master_process.py` is using a different port than `33400`, you will have to update the above `-o` parameter to accommodate this. The first line output to the command line by `master_process.py` on a given Pi (i.e. "THIS INTERFACE 10.35.70.20:33400") will tell you the port being used. This applies for all instructions below, too.

On other Pis, you can continue adding more instances (making sure update the `-o` parameter to point to the IP:PORT of each other currently active Pi)

Pi 40: `python3 master_process.py -c 5 -r 8 -a 10 -i 10.35.70.40 -o "{ '10.35.70.20:33400', '10.35.70.21:33400' }" -f out3`

Pi 41: `python3 master_process.py -c 5 -r 8 -a 10 -i 10.35.70.41 -o "{ '10.35.70.20:33400', '10.35.70.21:33400', '10.35.70.40:33400' }" -f out4`

You can add some other locations/namespaces to the network too:

Pi 42: `python3 master_process.py -c 5 -r 8 -a 10 -i 10.35.70.42 -o "{ '10.35.70.20:33400', '10.35.70.21:33400', '10.35.70.40:33400', '10.35.70.41:33400' }" -f out5 -l "53.291,-6.766"`

Pi 43: `python3 master_process.py -c 5 -r 8 -a 10 -i 10.35.70.43 -o "{ '10.35.70.20:33400', '10.35.70.21:33400', '10.35.70.40:33400', '10.35.70.41:33400', '10.35.70.42:33400' }" -f out6 -l "53.291,-6.766"`

You can disconnect a Pi and the other Pis will be able to immediately adapt to this.

**NOTE**: Again, remember to run `killall python3` when finished running the application on a Pi.