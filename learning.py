import numpy as np
import pymongo
import json


def createAttributeCollection(log):
	attributesCollection = []
	for document in log.find():
		for attribute in document.keys():
			if attribute not in attributesCollection:
				attributesCollection.append(attribute)
	if '_id' in attributesCollection:
		attributesCollection.remove('_id')
	if '_Id' in attributesCollection:
		attributesCollection.remove('_Id')
	if '_ID' in attributesCollection:
		attributesCollection.remove('_ID')
	if 'output' in attributesCollection:
		attributesCollection.remove('output')
	if 'Output' in attributesCollection:
		attributesCollection.remove('Output')
	if 'OUTPUT' in attributesCollection:
		attributesCollection.remove('OUTPUT')
	return attributesCollection


################################################################
# mean of an array
def mean(a):
	avg = float(sum(a))/float(len(a))
	return avg


################################
# standard deviation of an array
def stdev(a):
	return np.std(a)


################################
# calculate the stadardized value of a variable a knowing the mean and the standard deviation
def standardized(a, mean, stdev):
	return (a-mean)/stdev


################################
#calculate the normalized value (standardized + rescaled between o and 1)
def normalized(a, mean, stdev, a_max, a_min):
	if (a == 0 and mean == 0 and stdev == 0 and a_max == 0 and a_min == 0):
		return 0
	if not (a < a_max):
		return 1
	if not (a > a_min):
		return 0
	a_standardized = standardized(a, mean, stdev)
	a_max_standardized = standardized(a_max, mean, stdev)
	a_min_standardized = standardized(a_min, mean, stdev)
	return (a_standardized-a_min_standardized)/(a_max_standardized-a_min_standardized)

################################
# calculate a standardized array
def standardized_a(a):
	a_standardized = []
	for value in a:
		value_standardized = standardized(value, mean(a), stdev(a))
		a_standardized.append(value_standardized)
	return a_standardized


################################
# calculate the normalized array
def normalized_a(a):
	a_normalized = []
	for value in a:
		value_normalized = normalized(value, mean(a), stdev(a), max(a), min(a))
		a_normalized.append(value_normalized)
	return a_normalized

#################################################################
if __name__ == "__main__":
	# Setup MongoDB Collections
	db = pymongo.MongoClient("mongodb://localhost:27017")
	logs = db["log"]["input"]
	db_d = "mmt-rca"
	db_dest = db[db_d]
	known_state = db_dest["data_knowledge"]
	learning_indicators = db_dest["learning_indicators"]
	outputLabel = 'Output'
	minOutput = logs.find_one({}, sort=[(outputLabel, 1)])[outputLabel]
	maxOutput = logs.find_one({}, sort=[(outputLabel, -1)])[outputLabel]
	listAttributesCollection = createAttributeCollection(logs)
	for problemIndex in range(int(minOutput), int(maxOutput+1)):
		listAttributes = [[] for _ in range(len(listAttributesCollection))]
		# Inserting Log Features into arrays
		for idx, entry in enumerate(logs.find({outputLabel: problemIndex})):
			for i, attribute in enumerate(listAttributesCollection):
				if attribute in entry:
					value = entry[attribute]
					listAttributes[i].append(value)
		# Cleaning variables
		del i
		del attribute
		del entry
		del idx
		del value

		# Creating the "data_knowledge" collection,
		# in which for every feature it's saved the mean of the normalized array of original values
		problem = {}
		problem['_id'] = str(problemIndex)

		# Creating the "learning_indicators" collection,
		# in which for every feature it's saved the mean, the standard deviation and the min/max values
		indicators = {}
		indicators['_id'] = str(problemIndex)
		for i, attribute in enumerate(listAttributesCollection):
			problem[attribute] = str(mean(normalized_a(listAttributes[i])))
			indicators[attribute+'_mean'] = str(mean(listAttributes[i]))
			indicators[attribute+'_stdev'] = str(stdev(listAttributes[i]))
			indicators[attribute+'_max'] = str(max(listAttributes[i]))
			indicators[attribute+'_min'] = str(min(listAttributes[i]))
		del i
		del attribute
		known_state.insert_one(json.loads(json.dumps(problem)))
		learning_indicators.insert_one(json.loads(json.dumps(indicators)))
		print("Inserted state and indicator for Incident " + str(problemIndex))