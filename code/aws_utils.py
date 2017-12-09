import datetime
import boto3
import math
import sys

# approximate prices for U.S. East 1
AWS_INSTANCE_PRICES = {
    't2.nano': 0.0058,
    't2.micro': 0.0116,
    't2.small': 0.023,
    't2.medium': 0.0464,
    't2.large': 0.0928,
    't2.xlarge': 0.1856,
    't2.2xlarge': 0.3712,
    'm4.large': 0.1,
    'm4.xlarge': 0.2,
    'm4.2xlarge': 0.4,
    'm4.4xlarge': 0.8,
    'm4.10xlarge': 2,
    'm4.16xlarge': 3.2,
    'm3.medium': 0.067,
    'm3.large': 0.133,
    'm3.xlarge': 0.266,
    'm3.2xlarge': 0.532,
    'c5.large': 0.085,
    'c5.xlarge': 0.17,
    'c5.2xlarge': 0.34,
    'c5.4xlarge': 0.68,
    'c5.9xlarge': 1.53,
    'c5.18xlarge': 3.06,
    'c4.large': 0.1,
    'c4.xlarge': 0.199,
    'c4.2xlarge': 0.398,
    'c4.4xlarge': 0.796,
    'c4.8xlarge': 1.591,
    'c3.large': 0.105,
    'c3.xlarge': 0.21,
    'c3.2xlarge': 0.42,
    'c3.4xlarge': 0.84,
    'c3.8xlarge': 1.68,
    'p2.xlarge': 0.9,
    'p2.8xlarge': 7.2,
    'p2.16xlarge': 14.4,
    'p3.2xlarge': 3.06,
    'p3.8xlarge': 12.24,
    'p3.16xlarge': 24.48,
    'g2.2xlarge': 0.65,
    'g2.8xlarge': 2.6,
    'g3.4xlarge': 1.14,
    'g3.8xlarge': 2.28,
    'g3.16xlarge': 4.56,
}


def get_list_percentile(items, percentile):
    sorted_items = sorted(items)
    return sorted_items[int(math.floor(len(items) * percentile/100.0))]


def get_on_demand_price(inst_type):
    return AWS_INSTANCE_PRICES.get(inst_type, -1)


def get_on_demand_price(inst_type):
    return AWS_INSTANCE_PRICES.get(inst_type, -1)


def get_instance_types():
    now = datetime.datetime.utcnow()
    previous_time = now - datetime.timedelta(minutes=5)

    client = boto3.client('ec2')
    response = client.describe_spot_price_history(
        DryRun=False,
        StartTime=previous_time,
        EndTime=now,
        ProductDescriptions=['Linux/UNIX'],
        MaxResults=1000
    )
    sph_list = response['SpotPriceHistory']
    instances = set([sph['InstanceType'] for sph in sph_list])
    return instances


def get_spot_prices(inst_type, minutes=5):
    ''' get spot prices
    '''
    now = datetime.datetime.utcnow()
    previous_time = now - datetime.timedelta(minutes=minutes)

    client = boto3.client('ec2')
    response = client.describe_spot_price_history(
        DryRun=False,
        StartTime=previous_time,
        EndTime=now,
        InstanceTypes=[inst_type],
        ProductDescriptions=['Linux/UNIX'],
        MaxResults=100
    )
    sph_list = response['SpotPriceHistory']
    if len(sph_list) == 0:
        sys.exit('Cannot get spot prices for instance type {}'.format(
            inst_type))
    return [float(sph['SpotPrice']) for sph in sph_list]


def get_spot_price_stats(inst_type):
    sph = get_spot_prices(inst_type)

    out = [
        'Percentile prices for {}'.format(inst_type),
        'on-demand     {:.2f}'.format(get_on_demand_price(inst_type)),
        'maximum       {:.2f}'.format(max(sph)),
        '90 percentile {:.2f}'.format(get_list_percentile(sph, 90)),
        '80 percentile {:.2f}'.format(get_list_percentile(sph, 80)),
        'mean          {:.2f}'.format(sum(sph)/float(len(sph))),
        'mininum       {:.2f}'.format(min(sph))
    ]
    return '\n'.join(out)
