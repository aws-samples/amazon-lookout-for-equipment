# Annotate your time series with LabelStudio
Amazon Lookout for Equipment uses the data from your sensors to detect abnormal 
equipment behavior, so you can take action before machine failures occur and 
avoid unplanned downtime. Lookout for Equipment only uses unsupervised approaches
and doesn't need any label to provide valuable insights. Yet, knowing past time
ranges where something went wrong can help increase the forewarning time Lookout
for Equipment can provide before an actual event of interest.

[**LabelStudio**](https://labelstud.io/) is an open source data labeling tools which
include several templates to deal with time series dataset. Use this folder to learn 
how to you integrate LabelStudio in your machine learning workflow in a SageMaker 
notebook instance.

You have two options to run this example: manual, or automatic.

If you want to learn how this integration works because you will further adapt it
afterward, you can do the following:
1. Log into your AWS account
2. Create a SageMaker notebook instance
3. Open a terminal and git clone this repository
4. Navigate into the `apps/annotation-label-studio/` folder
5. Open the `1-initialize-label-studio.ipynb` notebook and follow the instructions to run it
6. Open the `2-configure-label-studio.ipynb` and follow the instructions in it to learn how to
   configure your LabelStudio instance and start labeling an example dataset
   
If you'd rather focus on the labeling task itself, log into your AWS account 
and click on one of the following link to deploy a CloudFormation template:

CFT links

Once the deployment is done:
1. Go to the SageMaker console and open the freshly created notebook instance
2. Open the `2-configure-label-studio.ipynb` and follow the instructions in it to learn how to
   configure your LabelStudio instance and start labeling an example dataset