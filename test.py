import boto3, asyncio, telnetlib3
from botocore.exceptions import ClientError
from ec2_metadata import ec2_metadata

@asyncio.coroutine
def shell(reader, writer):
    ec2 = boto3.client('ec2')
    asg = boto3.client('autoscaling')
    instance_id = ec2_metadata.instance_id
    writer.write('\r\nWould you like to play a game? ')

    response = asg.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            'CP_PoC_asg'
        ]
    )
    desired=resp['AutoScalingGroups'][0]['DesiredCapacity']

    response = asg.set_desired_capacity(
        AutoScalingGroupName='CP_PoC_asg',
        DesiredCapacity=desired+1,
        HonorCooldown=True
    )
    inp = yield from reader.read(1)
    if inp:
        writer.echo(inp)
        writer.write('\r\nThey say the only way to win '
                     'is to not play at all.\r\n')
        yield from writer.drain()
    writer.close()
    scale_and_shutdown_instance()

def scale_and_shutdown_instance():
    ec2 = boto3.client('ec2')
    asg = boto3.client('autoscaling')
    instance_id = ec2_metadata.instance_id
    print('Detaching from the ASG')
    response = asg.detach_instances(
        InstanceIds=[
            instance_id,
        ],
        AutoScalingGroupName='CP_PoC_asg',
        ShouldDecrementDesiredCapacity=True
    )
    print('detached')
    print('Stopping the instance')
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
        print('Success', response)
    except ClientError as e:
        print('Error', e)

loop = asyncio.get_event_loop()
coro = telnetlib3.create_server(port=6023, shell=shell)
server = loop.run_until_complete(coro)
loop.run_until_complete(server.wait_closed())