# Nibras 

## Introduction 


### How many assets do I have in my environment ?

##### It looks like a simple question, but to answer it, you have to go through the tedious job of collecting the assets manually and keep them in a centralized location where you and your team can access and update entries frequently.

#####  Nibras is here to help you answer that question in the simplest way possible by connecting to your layer2 Cisco devices (Catalyst Switches) and returns the total number of your live assets. In addition to the total number of assets, Nibras yields other valuable information which assists you in getting a better understanding of your layer2 security posture such as:

- OS version.
- Enable password status.
- Total number of trunk ports on each switch.
- Port/Mac mapping for all switches.
- Total number of assets associated with each switch.


#####  Upon execution, Nibras generates two different output files (XLS and JSON).

## Installation 



##### For your convenience and ease of use, Nibras comes in two builds. The first build is a python script that can be executed from any platform that has Python3 installed. Moreover Nibras comes in a docker container form (docker-compose file is provided)

##### Nibras runs exclusively on Python3, so please make sure you have Python3+ version before running the tool. Use the following command to install any missing dependencies on your system:

```sh
pip install -r requiremnts.txt
```

## Usage


##### 1. Nibras parses the target systems data from an input file located under the input folder. Only CSV or XLS extensions are supported. The file must be named as either input.csv or input.xls.

##### XLS Input 
![XLS input sample](https://imgur.com/iW1dxnl.png)


##### CSV Input 
![CSV input sample](https://imgur.com/c67bade.png)



##### 2. Once the input file is ready, you can run the main script file as shown in the below screenshot:


##### 3. After execution, two output files will be generated under the output folder, one in XLS format and the other in JSON format.


##### The script reports any issues directly on the screen, so please make sure to observe the output of the script while it's running.




##### Execution 
![Execution sample](https://imgur.com/QT65K15.png)


##### XLS output
![XLS output](https://imgur.com/lq6k5mb.png)

##### JSON output
![JSON output](https://imgur.com/CpunyZz.png)

## Roadmap


- Integration with layer3 devices for more accurate results.
- Adding more support to other vendors.
- Publish asstes data using API server.
