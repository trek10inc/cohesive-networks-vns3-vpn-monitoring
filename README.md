# Monitoring script for VNS3 VPN tunnels

## Description

This repository contains the script vpn_monitor.py for monitoring VPN tunnels and store information about available tunnels status in DataDog. The script uses the API of the Cohesive Networks VNS3 VPN controller, as well as the Datadog API to send a custom metric to Datadog to create an alert if any VPN tunnel goes down.

## Deploying

To deploy, simply grab the [latest release](https://github.com/trek10inc/cohesive-networks-vns3-vpn-monitoring/releases/), upload the zip to Lambda and configure the environment variables, as described below.

### Initial Setup

- Navigate to Lambda in the same region as the VPN controller you are monitoring and create a function called `vns3_vpn_monitor`
- Upload the zip file and configure the function inside the VPC and proper subnets
- Add a security group (no incoming rules are needed; outgoing should be open, which is the default) and a role
- Navigate to the security group of the VNS3 and allow incoming traffic over port 8000 from the Lambda function's security group (a nested security group)
- The function should trigger every minute
- HANDLER should be `vpn_monitor.check_tunnels`

### Environment Configuration

**DD\_API\_KEY**: This variable is the Datadog API key, which is generated in in the Integrations section of Datadog. This links the Datadog metric to our customers’ Datadog accounts. You will find these keys in the `Integrations` > `APIs` section of your Datadog account.

**DD\_APP\_KEY**: The Datadog app key is required for custom metrics. 

**VPNENV**: This variable is a Datadog tag applied to all tunnels being monitored by this Lambda function (whether that be on one controller or multiple controllers). For example, if the VPN controller is in pre-production, then `VPNENV` can be equal to `preproduction`. A second Lambda function should then be launched to monitor the production VPN controller. In this scenario,`VPNENV` would be equal to `production`. These tags will be used when configuring the Datadog monitors.

**VPN_CONTROLLER1**: This variable has some additional logic and parsing behind it. It defines the VPN controller(s) to monitor and must be entered with these three parameters, separated by single spaces: `VNS3_HOST=<privateIPAddress> VNS3_API_USER=api VNS3_API_PASSWD=<APIPassword>`. In the variable, `CONTROLLER1` is a placeholder for any string. Remember that we are using the private IP here because the Lambda function is being launched within the VPC.

**VPN_CONTROLLER2 (optional)**: The function can monitor multiple VPN controllers within a single VPC. For example, maybe you want to maintain separate VPN controllers for connecting to different customer/vendor networks. All you need to do is add a second (or third, fourth, etc.) variable to configure monitoring on your second VPN controller. You can replace `CONTROLLER1` and `CONTROLLER2` with any string. Note that if you want to monitor both a production and pre-production controller, you should not use this variable; instead, create two separate Lambda functions and change the VPNENV accordingly. *Remember* that the value of each `VPN_` config environment variables is a space separated set of variables. **THIS MUST BE PERFECT**. No extra spaces or commas or anything.  For example, the variable `VPN_1` will equal `VNS3_HOST=192.0.0.10 VNS3_API_USER=api VNS3_API_PASSWD=S0m3P4ssW0rd` and a new variable, `VPN_2` can equal `VNS3_HOST=192.0.0.99 VNS3_API_USER=api99 VNS3_API_PASSWD=S0m3P4ssW0rd99`

Once the configurations are complete, run a test to make sure there are no errors.

## Datadog Monitors

Navigate to your Datadog account and create a new monitor with the following configurations. You should create a separate monitor for each Lambda function where the `VPNENV` variable is different:

1) Define metric

- `Get` shoud be set to `vpn.tunnel.status` 
- `from` should be set to `vpn_environment:<variableConfiguredAbove>` (`variableConfiguredAbove` will likely equal either preproduction or production, depending on the VPN controller you want to monitor)
- `excluding` equals `none`
- `min by` = `everything`
- Configure a `Simple Alert` (a `Multi Alert` would create a ticket for each individual tunnel that goes down. This may be desirable depending on your use case. For the majority of use cases, if one tunnel goes down, all tunnels will be down. Thus, a single alert makes more sense)
    
2) Alert Conditions section will vary based on the your use case and organization's monitoring policies

3) Say What's Happening section will vary based on your use case and organization's monitoring policies

## Building From Source
To install all requirements (before building a zip):

* Initialize venv: `virtualenv venv`
* run `pip install -t vendored -r requirements.txt`