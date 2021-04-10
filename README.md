# Amazon Lookout for Equipment Samples

Amazon Lookout for Equipment uses the data from your sensors to detect abnormal 
equipment behavior, so you can take action before machine failures occur and 
avoid unplanned downtime.

This repository contains notebooks and examples on how to onboard and use
various features of Amazon Lookout for Equipment. At the moment, it only contains
the getting started guides, but this repository will be soon populated with various
content and samples that will help you better integrate the services:

```sh
. lookout-for-equipment
|
├── data/                                
|   # This directory will be generated when you will run the the
|   # different samples available in this repository.
|
├── apps/
|   # Will contain apps showcasing how to integrate Amazon Lookout
|   # for Equipment insights into your own applications and business
|   # process.
|
├── blogs/ (*COMING SOON*)
|   # Technical content associated to blog posts AWS writes about
|   # Amazon Lookout for Equipment will be hosted here.
|
├── getting_started/ (*NEW*)
|   # These notebooks can be used to follow along the getting started 
|   # section of the documentation.
|
├── integration
|   # You will find here some code snippets and templates showcasing
|   # how you can integrate with larger industrial ecosystems (connectivity
|   # to various data historians for instance).
|
├── model-evaluation
|   # These code snippets will show how to post-process your model results,
|   # how to monitor inferences and perform model continuous improvement.
|
├── model-training
|   # Training and improving models will be a key part of getting great
|   # insights your plants will be able to leverage to reinforce their
|   # maintenance practices.
|
├── preprocessing
|   # Multivariate industrial time series data can be challenging to deal
|   # with: these samples will show you how to explore your data, improve
|   # data quality, label your anomalies (manually or automatically), etc.
|
└── utils/
    |
    └── lookout_equipment_utils.py (*NEW*)
```

## Getting started notebooks
This folder contains various examples covering Amazon Lookout for Equipment best
practices. Open the **[getting_started](getting_started)** folder to find all the
ressources you need to train your first anomaly detection model. The notebooks 
provided can also serve as a template to build your own models with your own data.

In the **[getting_started](getting_started)** folder, you will learn to:

1. Prepare your data for use with Amazon Lookout for Equipment
2. Create your own dataset
3. Train a model based on this dataset
4. Evaluate a model performance and get some diagnostics based on historical data
5. Build an inference scheduler and post-process the predictions
6. Clean the ressources created by Amazon Lookout for Equipment

## Security

See [**CONTRIBUTING**](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This collection of notebooks is licensed under the MIT-0 License. See the
[**LICENSE**](LICENSE) file.