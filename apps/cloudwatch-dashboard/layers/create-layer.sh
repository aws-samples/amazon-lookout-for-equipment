#!/bin/bash

PACKAGE=$1
echo "Creating zip package for Lambda layer with '$PACKAGE'"

mkdir $PACKAGE
cd $PACKAGE
virtualenv --python=/usr/bin/python3.8 v-env
source v-env/bin/activate
python3.8 -m pip install $PACKAGE
deactivate
cd v-env/lib64/python3.8/site-packages
find -name "tests" -type d | xargs rm -rf
find -name "__pycache__" -type d | xargs rm -rf
cd ../../../..
mkdir python
cd python
cp -r ../v-env/lib64/python3.8/site-packages/* .
cd ..
zip -q -r "$PACKAGE-py38".zip python

#aws lambda publish-layer-version --layer-name $PACKAGE --zip-file fileb://"$PACKAGE".zip --compatible-runtimes python3.8