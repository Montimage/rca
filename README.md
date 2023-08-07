# MMT-RCA

## Architecture

The ***Root Cause Analysis*** tool is a systematic process for identifying root causes of problems or events and an approach for responding to them.

The system relies on algorithms to identify the most probable causes of detected anomalies based on the knowledge of similarly observed ones.

The workflow of the tool is composed of two stages:

1. *Learning phase*: the tool learns the state of the _already known_ problems and store those states into a db
2. *Monitoring phase*: the tool tests new incidents trying to compare the new with all the known ones.

## Code

To use this tool, you need to follow some steps.
First of all, you need to collect the data that describe your problems. It could be of any shape, form and extension.
Secondly, you need to parse the data into a csv (in that case, all the columns will be the features) or a JSON (the keys will be the features), so that each incident is described by all the columns.
**N.B.:** each incident must be described by only **one single row**.

In this repo I provide also a Python script called *parse_csv.py* which will take as input a folder containing various csvs related to problems and will derive a row for each problem.
This script can also apply *data augmentation* in case the number of examples per problems is too low: the more rows describing each problem you have, the more accurate is the tool!
In output.csv you can find an example of output of this script. In output_extra.csv you will find an example of output of this script at which it was applied data augmentation.

Your csv or your JSON file should be imported to a MongoDB collection.

It's time to focus on the [learning.py](https://github.com/Montimage/rca/blob/master/learning.py) script. In the setup phase of this script, it will try to connect to the MongoDB collection where you previously uploaded your incidents.
For each problem found in the collection, the script will separate them accordingly to their problemID (or output as is called in output.csv).
Then, the script will create two collections, one called *data_knowledge* which will include the mean of the states of the incidents, and another called _learning_indicators_ that instead includes the parameters to compute the Gaussian distribution for the new problems.

The [monitoring.py](https://github.com/Montimage/rca/blob/master/monitoring.py) script has the purpose of compare new problems with the states included in the *data_knowledge* collection. It will get all the new problems from the *raw_data_real_time* collection, where you should upload your *test* problems (same format as the ones used inside the learning phase).
It will compute a Gaussian distribution by using the parameters of every element included inside the *learning_indicators* collection; therefore, it will measure the similarity between the just computed distribution with each of the *data_knowledge* state, and outputs, inside the *report* collection, the most similar problem (indicated as *KnownIncidentID*), the *Similarity Score* and the *Proof*.
Inside the script you will also find some lines that will allow to apply **feature selection** operation, in order to remove those irrelevant attributes (I suggest you to think about the features to remove and to test a lot! :) )
