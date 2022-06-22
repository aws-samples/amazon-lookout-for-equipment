# Unsupervised anomaly prediction: From shop floors to deep space

## Welcome
Welcome to Re:MARS 2022!!  We are excited to get started.  Below are the instructions to get your accounts set up.  We will be starting shortly

## Event Engine AWS Account access

Go to: https://dashboard.eventengine.run/login .  You will be redirected to the page below.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image43.png)

Enter the event hash you have received from your instructor.

```
99ce-13d3c01bc4-83
```

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image44.png)

Click on Email One-Time Password (OTP).

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image45.png)

You are redirected to the following page:

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image46.png)

Enter your email address and click on Send passcode.  Next, you'll be redirected to the following page:

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image48.png)

Check your mailbox, copy-paste the one-time password and click on Sign in.  Next, you'll be redirected to the Team Dashboard. Click on AWS Console.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image50.png)

On the next screen, click on Open AWS Console.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image51.png)

You are then redirected to the AWS Console.

## Amazon SageMaker Studio Access

Amazon SageMaker Studio is a web-based, integrated development environment (IDE) for machine learning that lets you build, train, debug, deploy, and monitor your machine learning models. Studio provides all the tools you need to take your models from experimentation to production while boosting your productivity.

Open AWS console and verify the region is N. Virginia (us-east-1) in the upper right corner.  Under services search for Amazon SageMaker.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image23.png)

Under Get Started, click on the orange button SageMaker Studio.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image41.png)

A SageMaker Studio environment should already be provisioned. Click on Launch App > Studio (on the right side of the preprovisioned sagemakeruser username).

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image41.png)

The page can take 1 or 2 minutes to load when you access SageMaker Studio for the first time.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image30.png)

You will be redirected to the launcher tab that looks like this: 

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image31.png)

Under Notebooks and compute resources, make sure that the Data Science SageMaker image is selected and click on Notebook - Python 3.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image32.png)

This will open a new Untiled.ipynb notebook.  Click on the Launch Terminal in current SageMaker Image icon. The kernel must be fully started (the circle on the right next to the Share button must be empty) to be able to click on the icon.

![](https://static.us-east-1.prod.workshops.aws/public/f1fbbb1d-9df4-4a13-95bc-b00108a8c2c4/static/prerequisites/image36.png)

In the terminal, type the following command:

```
git clone https://github.com/aws-samples/amazon-lookout-for-equipment.git
```

Congratulations!!  Let's now start the labs!!!

