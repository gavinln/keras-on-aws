from __future__ import print_function

import os
import sys
import datetime
import csv
import pprint
import urllib
import configparser
from collections import OrderedDict

import boto3
from botocore.exceptions import ClientError

from IPython import embed
from invoke import task

from pathlib import Path
from collections import namedtuple

from storm import ConfigParser

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

from aws_utils import get_spot_price_stats
from aws_utils import get_instance_types
from aws_utils import get_on_demand_price

INSTANCE_TYPE = 't2.micro'
INSTANCE_PRICE = 0.05
IMAGE_ID = 'ami-82f4dae7'  # Ubuntu Server 16.04 LTS (HVM), SSD VolType 64 bit
SECURITY_GROUP_ID = 'sg-50664438'

#  aws ec2 describe-images --filters "Name=name,Values=Deep Learning AMI (Ubuntu)*" | jq '.Images[] | [ .Name, .Description, .ImageId]'
def deep_learning_ami():
    return {
        'us-east-2': 'ami-e4f4c981',
    }


def printPython(obj):
    print(highlight(pprint.pformat(obj), PythonLexer(),
          TerminalFormatter()))


def get_default_vpc():
    ''' gets the default vpc

    returns None if cannot get the default vpc
    '''

    ec2 = boto3.client('ec2')
    Filters = [{'Name': 'isDefault', 'Values': ['true']}]
    desc_vpcs = ec2.describe_vpcs(Filters=Filters)
    vpcs = desc_vpcs['Vpcs']
    if len(vpcs) > 0 and vpcs[0]['IsDefault']:
        return vpcs[0]
    return None


def get_security_group_id(group_name):
    ''' returns security group id given name

    return None if group_name does not exist
    '''

    ec2 = boto3.client('ec2')
    try:
        response = ec2.describe_security_groups(GroupNames=[group_name])
        sgs = response['SecurityGroups']
        for sg in sgs:
            return sg['GroupId']
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
            return None
        raise e
    return None


def get_external_ip():
    external_ip = urllib.request.urlopen(
        'https://api.ipify.org').read().decode('utf8')
    return external_ip


def get_rclone_sftp(host, user, key_file):
    sftp_map = OrderedDict([
        ('type', 'sftp'),
        ('host', host),
        ('user', user),
        ('port', '22'),
        ('pass', ''),
        ('key_file', key_file)
    ])
    return sftp_map


def get_config_parser_section(config, section):
    ' given a configparser section name returns ordered dict of section '
    config_map = OrderedDict(
        (key, value) for key, value in config[section].items())
    return config_map


def set_config_parser_section(config, section, config_map):
    ' add/update section to a configparser file '
    if section not in config.sections():
        config.add_section(section)
    for key, value in config_map.items():
        config.set(section, key, value)


def add_hostname(host, hostname, id_file, overwrite=True):
    ' add or updates ssh details for host in the ssh config file '
    default_config = ConfigParser().get_default_ssh_config_file()
    ssh_config = ConfigParser(default_config)
    ssh_config.load()
    hosts = ssh_config.search_host(host)
    if len(hosts) > 0:
        if not overwrite:
            return False
        ssh_config.update_host(host, {
            'hostname': hostname,
            'identityfile': id_file})
    else:
        ssh_config.add_host(host, {
            'hostname': hostname,
            'identityfile': id_file,
            'port': '22',
            'user': 'ubuntu'})
    ssh_config.write_to_ssh_config()
    return True


def get_instance_addr(instanceId):
    ec2 = boto3.client('ec2')
    output = ec2.describe_instances(InstanceIds=[instanceId])
    # printPython(output)

    reservations = output.get('Reservations')
    if reservations and len(reservations) > 0:
        reservation = reservations[0]
        instances = reservation.get('Instances')
        if instances and len(instances) > 0:
            instance = instances[0]
            addr = instance.get('PublicIpAddress')
            if not addr or len(addr) == 0:
                addr = instance.get('PrivateIpAddress')
    return addr


def check_environment(*args):
    out = []
    for arg in args:
        if arg not in os.environ:
            out.append('export {}='.format(arg))
    if len(out) > 0:
        out.insert(0, 'set environment variables')
        sys.exit('\n'.join(out))


CredentialHeader = namedtuple('CredentialHeader', [
    'User_name', 'Password', 'Access_key_ID', 'Secret_access_key'])


@task(name='configure',
      help={'credentials_file': 'Full credentials file path'})
def configure(ctx, credentials_file):
    ' set credentials '
    cred_file = Path(credentials_file)
    if not cred_file.is_file():
        sys.exit('{} is not a file'.format(cred_file))
    with cred_file.open() as csv_file:
        for idx, row in enumerate(csv.reader(csv_file, delimiter=',')):
            if idx == 1:
                credentials = CredentialHeader(*row[:4])
    cmd = 'aws configure set aws_access_key_id {}'.format(
        credentials.Access_key_ID)
    ctx.run(cmd)
    cmd = 'aws configure set aws_secret_access_key {}'.format(
        credentials.Secret_access_key)
    ctx.run(cmd)


def get_keyPair(keyPairs, keyName):
    ' returns keypair if keyname in keypair list otherwise None '
    for keyPair in keyPairs:
        if keyPair['KeyName'] == keyName:
            return keyPair
    return None


@task(name='csg', help={})
def create_security_group(ctx):
    ''' create security group keras-vm in default vpc

        returns existing security_group id if exists
        otherwise creates new security group and returns id
    '''

    security_group_name = 'keras-vm'
    sg_id = get_security_group_id(security_group_name)
    if sg_id:
        print(sg_id)
        return

    ec2 = boto3.client('ec2')
    default_vpc = get_default_vpc()
    if not default_vpc:
        print('Cannot find default vpc')
        return

        vpc_id = default_vpc['VpcId']
        description = 'security group for keras-on-aws'
        sg = ec2.create_security_group(
            Description=description, GroupName=security_group_name,
            VpcId=vpc_id)
        security_group = boto3.resource('ec2').SecurityGroup(sg['GroupId'])
        external_ip = get_external_ip()
        cidr_ip = external_ip + '/32'
        security_group.authorize_ingress(
            CidrIp=cidr_ip, FromPort=22, IpProtocol='tcp', ToPort=22)
        print(sg['GroupId'])
    else:
        print('Cannot find default vpc')


@task(name='del-sg', help={})
def delete_security_group(ctx, security_group_id=None):
    ' delete security group keras-vm '

    ec2 = boto3.client('ec2')
    ec2.delete_security_group(GroupName='keras-vm')


@task(name='ckp', help={'name': 'key pair name'})
def create_key_pair(ctx, name):
    ' create key pair '
    ec2 = boto3.client('ec2')
    response = ec2.describe_key_pairs()
    keyPairs = response.get('KeyPairs', None)
    if keyPairs:
        keyPair = get_keyPair(keyPairs, name)
        if keyPair:
            ec2.delete_key_pair(KeyName=name)
    # no keypairs exist
    response = ec2.create_key_pair(KeyName=name)
    print(response['KeyMaterial'])


@task(name='dis')
def describe_instances(ctx):
    ' describe instances '
    aws_cmd = 'aws ec2 describe-instances'
    jq_cmd = 'jq -C ".Reservations[].Instances[] | ' \
        '{InstanceType, KeyName, State: .State.Name, PublicIpAddress, ' \
        'InstanceId, ImageId, LaunchTime, Zone: .Placement.AvailabilityZone }"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dvp')
def describe_vpcs(ctx):
    ' describe vpcs'
    aws_cmd = 'aws ec2 describe-vpcs'
    jq_cmd = 'jq -C ".Vpcs[] | { VpcId, State, IsDefault, CidrBlock }"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dkp')
def describe_key_pairs(ctx):
    ' describe key pairs '
    aws_cmd = 'aws ec2 describe-key-pairs'
    jq_cmd = 'jq -c -C ".KeyPairs[]"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dig')
def describe_internet_gateways(ctx):
    ' describe internet gateways '
    aws_cmd = 'aws ec2 describe-internet-gateways'
    jq_cmd = 'jq -C ".InternetGateways[] | ' \
        '{ InternetGatewayId, Attachments}"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dsgs')
def describe_security_groups(ctx):
    ' describe security groups '
    aws_cmd = 'aws ec2 describe-security-groups'
    jq_cmd = 'jq -cC ".SecurityGroups[] | ' \
        '{ GroupId, GroupName }"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dsg', help={
    'security-group-id': 'Security group for image'})
def describe_security_group(ctx, security_group_id):
    ' describe security group '
    aws_cmd = ['aws ec2 describe-security-groups',
               ' --group-ids {}']
    aws_cmd = ''.join(aws_cmd).format(security_group_id)
    jq_cmd = 'jq -C ".SecurityGroups[] | ' \
        '{ GroupId, GroupName, VpcId, OwnerId, Description }"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='ri', help={
    'inst-type': 'type of EC2 instance (default: {})'.format(INSTANCE_TYPE),
    'image-id': 'AMI image of instance (default: {})'.format(IMAGE_ID),
    'security-group-id': 'Security group for image (default: {})'.format(
        SECURITY_GROUP_ID)})
def run_instances(
        ctx, security_group_id,
        inst_type=INSTANCE_TYPE,
        image_id=IMAGE_ID):
    ' run instances '
    check_environment('KEY_NAME')
    key_name = os.environ['KEY_NAME']
    aws_cmd = [' aws ec2 run-instances --image-id {} --count 1 ',
               ' --instance-type {} --key-name {} --security-group-ids {} ']
    aws_cmd = ''.join(aws_cmd).format(
        image_id, inst_type, key_name, security_group_id)

    jq_cmd = 'jq -C "."'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='ti', help={'inst-id': 'instance id'})
def terminate_instances(ctx, inst_id):
    ' terminate instances '
    aws_cmd = 'aws ec2 terminate-instances --instance-ids {}'
    aws_cmd = aws_cmd.format(inst_id)
    jq_cmd = 'jq -C "."'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='ssh-init', help={'inst-id': 'instance id'})
def ssh_init(ctx, inst_id):
    ' add to ssh config '
    check_environment('ANSIBLE_PRIVATE_KEY_FILE')
    id_file = os.environ['ANSIBLE_PRIVATE_KEY_FILE']

    addr = get_instance_addr(inst_id)
    add_hostname('keras', addr, id_file, overwrite=True)


@task(name='rclone-init', help={'inst-id': 'instance id'})
def rclone_init(ctx, inst_id):
    ' add to rclone config '
    check_environment('ANSIBLE_PRIVATE_KEY_FILE')
    id_file = os.environ['ANSIBLE_PRIVATE_KEY_FILE']

    addr = get_instance_addr(inst_id)
    # modify rclone config ~/.config/rclone/rclone.conf
    result = ctx.run('rclone config file', hide=True)
    if result.ok:
        out = [line for line in result.stdout.split('\n') if len(line) > 0]
        rclone_conf = out[-1]
        config = configparser.ConfigParser()
        config.read(rclone_conf)
        # for section in config.sections():
        #     config_map = get_rclone_sftp(ip_inst, 'ubuntu', id_file)
        #     if section == 'keras':
        #         # may need to do something different here
        #         config_map = get_config_parser_section(config, section)
        #         set_config_parser_section(config, section, config_map)
        #     else:
        #         set_config_parser_section(config, section, config_map)
        with open(rclone_conf, 'w') as f:
            config.write(f)
    else:
        print('rclone not installed or not in PATH')


@task(name='tunnel', help={'inst-id': 'instance id'})
def tunnel(ctx, inst_id):
    ' tunnel to instance redirecting port 8888 '
    # addr = get_instance_addr(inst_id)
    cmd = 'ssh -L 0.0.0.0:8888:localhost:8888 keras'
    ctx.run(cmd, pty=True)


@task(name='dv')
def describe_volumes(ctx):
    ' describe volumes '
    aws_cmd = 'aws ec2 describe-volumes'
    jq_cmd = 'jq -c -C ".Volumes[] '\
        ' | { Size, VolumeId, State, AttachTime:.Attachments[].AttachTime } "'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='sps', help={
    'inst-type': 'Type of EC2 instance (default: {})'.format(INSTANCE_TYPE)}
)
def spot_price_stats(ctx, inst_type=INSTANCE_TYPE):
    ' display spot price statistics '
    result = get_spot_price_stats(inst_type)
    print(result)


@task(name='rsi', help={
    'security-group-id': 'Security group for image',
    'price': 'price per hour of instance',
    'inst-type': 'type of EC2 instance (default: {})'.format(INSTANCE_TYPE),
    'image-id': 'AMI image of instance (default: {})'.format(IMAGE_ID)})
def request_spot_instances(
        ctx, security_group_id, price,
        inst_type=INSTANCE_TYPE,
        image_id=IMAGE_ID,
        ):
    ' request spot instances '
    check_environment('KEY_NAME')
    key_name = os.environ['KEY_NAME']

    price_num = float(price)
    if price_num > 0.91:
        sys.exit('spot price of {} is too high'.format(price_num))

    # TODO: Explore using "DeleteOnTermination": false,
    launch_specification = '''
        {{
          "KeyName": "{}",
          "ImageId": "{}",
          "SecurityGroupIds": [ "{}" ],
          "InstanceType": "{}",
          "BlockDeviceMappings": [
           {{
              "DeviceName": "/dev/sda1",
              "Ebs": {{
                "DeleteOnTermination": true,
                "VolumeType": "gp2",
                "VolumeSize": 64
              }}
            }}
          ]
        }}
    '''.format(key_name, image_id, security_group_id, inst_type)
    ls_encode = launch_specification.replace('\n', '')
    ls_encode = ls_encode.replace('"', '\\"')
    aws_cmd = 'aws ec2 request-spot-instances --spot-price "{}" ' \
        '--instance-count 1 --type "one-time" --launch-specification "{}"'
    aws_cmd = aws_cmd.format(price_num, ls_encode)
    jq_cmd = 'jq -c -C "."'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dsir')
def describe_spot_instance_requests(ctx):
    ' describe spot instance requests '
    aws_cmd = 'aws ec2 describe-spot-instance-requests'
    jq_cmd = 'jq -c -C ".SpotInstanceRequests[] | ' \
        '{Code:.Status.Code, SpotPrice, RequestId:.SpotInstanceRequestId, ' \
        'InstanceType:.LaunchSpecification.InstanceType}"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='sph', help={
    'inst-type': 'Type of EC2 instance'}
)
def spot_price_history(ctx, inst_type):
    ' spot price history '
    instance_types = get_instance_types()
    if inst_type not in instance_types:
        sys.exit('inst-type should be one of {}'.format(
            ', '.join(sorted(instance_types))
        ))
    now = datetime.datetime.utcnow()
    # start_time = '{:%Y-%m-%dT%H:00:00}'.format(now)
    previous_time = now - datetime.timedelta(minutes=5)
    start_time = '{:%Y-%m-%dT%H:%M:%S}'.format(previous_time)
    aws_cmd = 'aws ec2 describe-spot-price-history --start-time {} ' \
        '--product "Linux/UNIX" --instance-type "{}"'
    aws_cmd = aws_cmd.format(start_time, inst_type)
    jq_cmd = 'jq -c -C ".SpotPriceHistory[] | ' \
        '[.SpotPrice, .AvailabilityZone, .InstanceType ]"'
    sort_cmd = 'sort -r'
    cmd = '|'.join([aws_cmd, jq_cmd, sort_cmd])
    ctx.run(cmd)


@task(name='csir', help={
    'request-id': 'spot instance request id'}
)
def cancel_spot_instance_requests(ctx, request_id):
    ' cancel spot instance requests '
    aws_cmd = 'aws ec2 cancel-spot-instance-requests ' \
        '--spot-instance-request-ids {}'.format(request_id)
    jq_cmd = 'jq -c -C ".CancelledSpotInstanceRequests[] | ' \
        '{State, RequestId:.SpotInstanceRequestId}"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='disr')
def describe_instances_running(ctx):
    ' describe instances running '
    aws_cmd = 'aws ec2 describe-instances ' \
        '--filter Name=instance-state-name,Values=running'
    jq_cmd = 'jq -C ".Reservations[].Instances[]| ' \
        '{InstanceType, KeyName, State: .State.Name, PublicIpAddress, ' \
        'InstanceId, ImageId}"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='di', help={'inst-id': 'instance id'})
def describe_instance(ctx, inst_id):
    ' describe instance '
    aws_cmd = 'aws ec2 describe-instances --instance-id {}'
    aws_cmd = aws_cmd.format(inst_id)
    jq_cmd = '''
        jq -C ".Reservations[].Instances[]|
        {InstanceType, KeyName, State: .State.Name,
        PublicIpAddress, PrivateIpAddress, InstanceId, ImageId}"
    '''
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dt')
def describe_tags(ctx, resource_id):
    ' describe tags '
    aws_cmd = 'aws ec2 describe-tags --filter Name=resource-id,Values={}'
    aws_cmd = aws_cmd.format(resource_id)
    jq_cmd = '''
        jq -cC '.Tags[] | {Key, Value}'
    '''
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='dim')
def describe_images(ctx):
    ' describe images owned by self '
    aws_cmd = 'aws ec2 describe-images --owners self'
    jq_cmd = 'jq -C ".Images[] | {Name, ImageId, State, Description}"'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='cim', help={'inst-id': 'instance id'})
def create_image(ctx, inst_id, name, desc):
    ' create image '
    aws_cmd = 'aws ec2 create-image --instance-id {} --name "{}" ' \
        '--description "{}"'
    aws_cmd = aws_cmd.format(inst_id, name, desc)
    jq_cmd = 'jq -C "."'
    cmd = '|'.join([aws_cmd, jq_cmd])
    print(cmd)
    ctx.run(cmd)


@task(name='reboot', help={'inst-id': 'instance id'})
def reboot_instances(ctx, inst_id):
    ' reboot instances '
    aws_cmd = 'aws ec2 reboot-instances --instance-ids {}'
    aws_cmd = aws_cmd.format(inst_id)
    ctx.run(aws_cmd)


@task(name='stop', help={'inst-id': 'instance id'})
def stop_instances(ctx, inst_id):
    ' stop instances '
    aws_cmd = 'aws ec2 stop-instances --instance-ids {}'
    aws_cmd = aws_cmd.format(inst_id)
    jq_cmd = 'jq -C "."'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='start', help={'inst-id': 'instance id'})
def start_instances(ctx, inst_id):
    ' start instances '
    aws_cmd = 'aws ec2 start-instances --instance-ids {}'
    aws_cmd = aws_cmd.format(inst_id)
    jq_cmd = 'jq -C "."'
    cmd = '|'.join([aws_cmd, jq_cmd])
    ctx.run(cmd)


@task(name='get-ip', help={'inst-id': 'instance id'})
def get_ip(ctx, inst_id):
    ' get ip address '

    print(get_instance_addr(inst_id))
