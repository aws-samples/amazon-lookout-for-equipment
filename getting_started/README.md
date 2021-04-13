# Amazon Lookout for Equipment Getting Started.
Amazon Lookout for Equipment uses the data from your sensors to detect abnormal equipment behavior, so you can take action before machine failures occur and avoid unplanned downtime.

**Note:** *Expect between 1.5 and 2.5 hours to run this whole set of notebooks, including:*
* *Between 30 and 45 minutes of training time*
* *1 hour of scheduled inference to get enough relevant results to analyze (you can stop after the first inference is generated after 5 minutes though)*

## Overview
Amazon Lookout for Equipment analyzes the data from your sensors, such as pressure, flow rate, RPMs, temperature, and power to automatically train a specific ML model based on just your data, for your equipment – with no ML expertise required. Lookout for Equipment uses your unique ML model to analyze incoming sensor data in real-time and accurately identify early warning signs that could lead to machine failures. This means you can detect equipment abnormalities with speed and precision, quickly diagnose issues, take action to reduce expensive downtime, and reduce false alerts.

### Installation instructions
[**Create an AWS account**](https://portal.aws.amazon.com/gp/aws/developer/registration/index.html) if you do not already have one.

Once you have access to the service, login to your AWS account and navigate to the SageMaker console and create a new instance. Using an **ml.t3.medium** instance with the standard 5 GB attached EBS volume is enough to process and visualize the dataset comfortably. To enable exploration of big timeseries dataset, you might need to increase the EBS volume size. Some plots can take up a significant amount of memory: in such exploration, it's not unusual to move to bigger memory optimized instance (like the **ml.m5.xlarge** one), but that won't be necessary for this tutorial.

You need to ensure that this notebook instance has an **IAM role** which allows it to call the Amazon Lookout for Equipment APIs:

1. In your **IAM console**, look for the SageMaker execution role endorsed by your notebook instance (a role with a name like `AmazonSageMaker-ExecutionRole-yyyymmddTHHMMSS`)
2. On the `Permissions` tab, click on `Attach policies`
3. In the Filter policies search field, look for `AmazonLookoutEquipmentFullAccess`, tick the checkbox next to it and click on `Attach policy`
4. Browse to the `Trust relationship` tab for this role, click on the `Edit trust relationship` button and fill in the following policy. You may already have a trust relationship in place for this role, in this case, just add the **"lookoutequipment.amazonaws.com"** in the service list:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "sagemaker.amazonaws.com",
            
          // ... Other services
            
          "lookoutequipment.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
5. Click on `Update the Trust Policy`: your SageMaker notebook instance can now call the Lookout for Equipment APIs and the service will have the appropriate access to the S3 buckets where the data will be located.

You can know navigate back to the Amazon SageMaker console, then to the Notebook Instances menu. Start your instance and launch either Jupyter or JupyterLab session. From there, you can launch a new terminal and clone this repository into your environment using `git clone`.

Once you've cloned this repo, open the [**configuration file**](config.py) and update the bucket name you want to use to store the intermediate files generated throughout this tutorial. You can leave all the other parameters to their default values.

### Repository structure
Browse to the [**data preparation**](1_data_preparation.ipynb) notebook: this first notebook will download and prepare the data necessary before you move to other ones:

```
.
|
├── README.md                          <-- This instruction file
|
├── assets/                            <-- Pictures used throughout the notebooks
|
├── 1_data_preparation.ipynb           <-- START HERE: data preparation notebook, useful to
|                                          download and prepare the data, get familiar with
|                                          them
├── 2_dataset_creation.ipynb           <-- Create a Lookout for Equipment dataset
├── 3_model_training.ipynb             <-- Train a Lookout for Equipment model
├── 4_model_evaluation.ipynb           <-- Plot the evaluation results and some diagnostics
├── 5_inference_scheduling.ipynb       <-- Schedule a regular inference execution and plot
|                                          the obtained results
├── 6_cleanup.ipynb                    <-- Cleanup the resources created in this tutorial
|
└── utils/
    └── lookout_equipment_utils.py     <-- Utilities to manage Lookout for Equipment assets
```

## Questions

Please contact [**Michaël HOARAU**](mailto:michoara@amazon.fr) or raise an issue on this repository.

## Security

See [**CONTRIBUTING**](CONTRIBUTING.md#security-issue-notifications) for more information.

## License
This collection of notebooks is licensed under the MIT-0 License. See the LICENSE file.