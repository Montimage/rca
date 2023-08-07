from scipy import spatial
from scipy.spatial import distance
from scipy.spatial.distance import jaccard
from scipy.spatial.distance import minkowski
from scipy.spatial.distance import cityblock
import numpy as np
import pymongo
import time
from learning import createAttributeCollection

###################################################
def cosine_similarity(a1, a2):
    return 1 - spatial.distance.cosine(a1, a2)


##################################################
def adjusted_cosine_similarity(a1, a2):
    mean_a1a2 = (np.sum(a1 + a2)) / (len(a1) + len(a2))
    return (1 - spatial.distance.cosine(a1 - mean_a1a2, a2 - mean_a1a2))

##################################################
def adjusted_cosine_similarity2(a1, a2):
    mean_a1 = np.mean(a1)
    mean_a2 = np.mean(a2)
    return (1 - spatial.distance.cosine(a1 - mean_a1, a2 - mean_a2))


##################################################
def jaccard_distance(a, b):
    return jaccard(a, b)


##################################################
def minkowski_distance(a, b):
    return minkowski(a, b, 3)


##################################################
# REMEMBER TO CHANGE SIMILARITY SCORE COMPUTATION -> THE LOWER THE DISTANCE, THE BETTER IS, SO PUT MINUS
def euclidean_distance(a1, a2):
    return distance.euclidean(a1, a2)


##################################################
def manhattan_distance(a, b):
    return cityblock(a, b)


##################################################
# standard deviation of an array
def stdev(a):
    return np.std(a)


################################
# calculate the stadardized value of a variable a knowing the mean and the standard deviation
def standardized(a, mean, stdev):
    if stdev > 0:
        return (a - mean) / stdev
    else:
        return 0


################################
# calculate the normalized value (standardized + rescaled between o and 1)
def normalized(a, mean, stdev, a_max, a_min):
    if not (a < a_max):
        return 1
    if not (a > a_min):
        return 0
    a_standardized = standardized(a, mean, stdev)
    a_max_standardized = standardized(a_max, mean, stdev)
    a_min_standardized = standardized(a_min, mean, stdev)
    if (a_max_standardized == a_min_standardized):
        return 0
    else:
        return (a_standardized - a_min_standardized) / (a_max_standardized - a_min_standardized)


# calculate a standardized array
def standardized_a(a):
    a_standardized = []
    for value in a:
        value_standardized = standardized(value, mean(a), stdev(a))
        a_standardized.append(value_standardized)
    return a_standardized


################################
def normalized_a(a):
    a_normalized = []
    for value in a:
        value_normalized = normalized(value, mean(a), stdev(a), max(a), min(a))
        a_normalized.append(value_normalized)
    return a_normalized


#################################################################

mongoClient = pymongo.MongoClient("mongodb://localhost:27017")
while 1:
    start_time = time.time()
    db_d = "mmt-rca"
    db_dest = mongoClient[db_d]
    known_state = db_dest["data_knowledge"]
    learning_indicators = db_dest["learning_indicators"]  # indicators to normalised monitoring data in real time
    new_state_raw = db_dest["raw_data_real_time"]  # raw data before being normalised
    report = db_dest["report"]
    readAttributes = True
    listAttributesCollection = []
    
    # This monitoring phase look at the "raw_data_real_time" collection for every new entry and take all the selected
    # features to be compared to the "learnt" data. The raw data is normalized for every feature
    # using the 4 indicators (which allow the Gaussian curve to be constructed)
    for raw_state in new_state_raw.find({}):
        known_incident_id = ""
        max_sim_score = 0 #initialized with high number if we chose one of the distances, with 0 if not
        sim_score = 0
        created = ""
        description = ""
        if readAttributes:
            readAttributes = False
            listAttributesCollection = createAttributeCollection(new_state_raw)
            # apply here the FEATURE SELECTION by removing the attributes you want to remove in the computation of the new state
            # if 'mdns' in listAttributesCollection:
            #     listAttributesCollection.remove('mdns')
        for indicators in learning_indicators.find({}):
            actual_problem = indicators['_id']
            curr_raw_state = []
            curr_normalised_state = []
            for attribute in  listAttributesCollection:
                curr_raw_state.append(raw_state[attribute])
                mean_a = float(indicators[attribute + "_mean"])
                stdev_a = float(indicators[attribute + "_stdev"])

                max_a = float(indicators[attribute + "_max"])
                min_a = float(indicators[attribute + "_min"])
                curr_normalised_state.append(normalized(raw_state[attribute], mean_a, stdev_a, max_a,
                                                        min_a))  # to be compared with old normalized states
            # after taking the current state to be classified, here it's saved the known state, made of the same feature
            # selected before
            for a_known_state in known_state.find():
                if a_known_state['_id'] == actual_problem:
                    normalised_known_state = []

                    for attribute in  listAttributesCollection:
                        normalised_known_state.append(float(a_known_state[attribute]))
                    sim_score = abs(cosine_similarity(curr_normalised_state, normalised_known_state))
                    # if a similirarity score is higher for a particoular indicator, this score is memorized and the
                    # corresponding id problem is taken in account
                    if (sim_score > max_sim_score): #lt if choosing distances, ht otherwise
                        max_sim_score = sim_score
                        known_incident_id = a_known_state["_id"]
        # inserting a new element with id, knownIncidentId, Similarity score and proof (the state of a known problem)
        new_report = {"_id": raw_state["_id"], "KnownIncidentID": known_incident_id,
                      "Similarity score": max_sim_score, "Proof": raw_state}
        report.insert_one(new_report)
        new_state_raw.delete_one({"_id": raw_state["_id"]})
        if known_incident_id != "0":
            print("An incident has been detected, is of type " + known_incident_id)
        # print(new_report)
    end_time = time.time()
    execution_time = end_time - start_time
    print("Execution time was: ", execution_time, "seconds.")
    time.sleep(5)