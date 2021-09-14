import boto3
import os
import json
iam = boto3.client('iam')
def crawlerRoleCreation(inference_data_input_arn_s3,inference_data_output_arn_s3):
    role_name_crawler= 'L4E_visualization'
    policy_name_crawler = 'AccessGlueForS3andL4E'
    print('newversion')
    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
              "Effect": "Allow",
              "Principal": {
                "Service": "glue.amazonaws.com"
              },
              "Action": "sts:AssumeRole"
            }
        ]
    }

    try:
        create_role_response = iam.create_role(
            RoleName = role_name_crawler,
            AssumeRolePolicyDocument = json.dumps(assume_role_policy_document)
        );

    except iam.exceptions.EntityAlreadyExistsException as e:
        print('Warning: role already exists:', e)
        create_role_response = iam.get_role(
            RoleName = role_name_crawler
        );
    role_arn = create_role_response["Role"]["Arn"]

    print('IAM Role: {}'.format(role_arn))

    policy_json={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": [
                    inference_data_input_arn_s3,
                    inference_data_output_arn_s3
                ]
            },
            {
                "Effect": "Allow",
                    "Action": [
                        "glue:*",
                        "s3:GetBucketLocation",
                        "s3:ListBucket",
                        "s3:ListAllMyBuckets",
                        "s3:GetBucketAcl",
                        "ec2:DescribeVpcEndpoints",
                        "ec2:DescribeRouteTables",
                        "ec2:CreateNetworkInterface",
                        "ec2:DeleteNetworkInterface",
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:DescribeSecurityGroups",
                        "ec2:DescribeSubnets",
                        "ec2:DescribeVpcAttribute",
                        "iam:ListRolePolicies",
                        "iam:GetRole",
                        "iam:GetRolePolicy",
                        "cloudwatch:PutMetricData"
                    ],
                    "Resource": [
                        "*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:CreateBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::aws-glue-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        "arn:aws:s3:::aws-glue-*/*",
                        "arn:aws:s3:::*/*aws-glue-*/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject"
                    ],
                    "Resource": [
                        "arn:aws:s3:::crawler-public*",
                        "arn:aws:s3:::aws-glue-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:logs:*:*:/aws-glue/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:CreateTags",
                        "ec2:DeleteTags"
                    ],
                    "Condition": {
                        "ForAllValues:StringEquals": {
                            "aws:TagKeys": [
                                "aws-glue-service-resource"
                            ]
                        }
                    },
                    "Resource": [
                        "arn:aws:ec2:*:*:network-interface/*",
                        "arn:aws:ec2:*:*:security-group/*",
                        "arn:aws:ec2:*:*:instance/*"
                    ]
                }
        ]
    }

    try:
        create_policy = iam.create_policy(
            PolicyName = 'AccessGlueForS3andL4E',
            PolicyDocument = json.dumps(policy_json)
        );

    except iam.exceptions.EntityAlreadyExistsException as e:
        print('Warning: role already exists:', e)
        response = iam.list_policies()
        s= response['Policies']
        my_policy = next((item for item in s if item['PolicyName'] == 'AccessGlueForS3andL4E'), None)
        create_policy = iam.get_policy(
            PolicyArn = my_policy['Arn']
        );

    policy_arn = create_policy["Policy"]["Arn"]
    print('IAM Policy: {}'.format(policy_arn))

    attach_response = iam.attach_role_policy(
        RoleName = role_name_crawler,
        PolicyArn = policy_arn
    );
    return (role_name_crawler,policy_arn)