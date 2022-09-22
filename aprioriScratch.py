
import numpy as np
def create_check(cluster,column_name,data):
  result = []
  for value in cluster[column_name]:
    avg = cluster[column_name].mean()
    if float(value) >= float(avg):
      string = str(column_name)+">=" + str(round(cluster[column_name].mean(),3))
      result.append(string) 
      
    else:
      string = str(column_name)+"<" + str(round(cluster[column_name].mean(),3))
      result.append(string)
  column_new = str(column_name) + "_check"
  cluster[column_new] = result 
  data[column_new]=result


def create_candidate_1(X):
    c1 = []
    for transaction in X:
        for t in transaction:
            t = frozenset([t])
            if t not in c1:
                c1.append(t)
    return c1

def aprioriFunc(X, min_support):
    c1 = create_candidate_1(X)
    freq_item, item_support_dict,freq_item_support_dict = create_freq_item(X, c1, min_support)
    freq_items = [freq_item]
    
    k = 0

    while len(freq_items[k]) > 0:
        freq_item = freq_items[k]
        ck = create_candidate_k(freq_item, k)       
        freq_item, item_support,freq_item_support = create_freq_item(X, ck, min_support)
        freq_items.append(freq_item)
        freq_item_support_dict.update(item_support)
        item_support_dict.update(item_support)
        
        k += 1
        
    return freq_items, item_support_dict,freq_item_support

def create_freq_item(X, ck, min_support):

    item_count = {}
    for transaction in X:
        for item in ck:
            if item.issubset(transaction):
                if item not in item_count: 
                    item_count[item] = 1
                else: 
                    item_count[item] += 1    
    
    n_row = X.shape[0]
    freq_item = []
    item_support = {}
    freq_item_support = {}

    for item in item_count:
        support = item_count[item] / n_row
        if support >= min_support:
            freq_item.append(item)
            freq_item_support[item]=support
        
        item_support[item] = support
        
    return freq_item, item_support,freq_item_support

from itertools import combinations
def create_candidate_k(freq_item, k):
    ck = []

    if k == 0:
        for f1, f2 in combinations(freq_item, 2):
            item = f1 | f2 # union of two sets
            ck.append(item)
    else:    
        for f1, f2 in combinations(freq_item, 2):       

            intersection = f1 & f2
            if len(intersection) == k:
                item = f1 | f2
                if item not in ck:
                    ck.append(item)
    return ck

def create_rules(freq_items, item_support_dict, min_confidence):
    association_rules = []
    for idx, freq_item in enumerate(freq_items[1:(len(freq_items) - 1)]):
        for freq_set in freq_item:
          
            subsets = [frozenset([item]) for item in freq_set]
            rules, right_hand_side = compute_conf(freq_items, item_support_dict, 
                                                  freq_set, subsets, min_confidence)
            association_rules.extend(rules)
            
            if len(right_hand_side) > 0:
                try:
                    if idx != 0:
                        k = 0
                        while len(right_hand_side[0]) < len(freq_set) - 1:
                            ck = create_candidate_k(right_hand_side, k = k)
                            rules, right_hand_side = compute_conf(freq_items, item_support_dict,
                                                          freq_set, ck, min_confidence)
                            association_rules.extend(rules)
                            k += 1    
                except (IndexError):
                    msg=1
            
    return association_rules

def compute_conf(freq_items, item_support_dict, freq_set, subsets, min_confidence):

    rules = []
    right_hand_side = []
    
    for rhs in subsets:
        lhs = freq_set - rhs
        conf = item_support_dict[freq_set] / item_support_dict[lhs]
        
        if conf >= min_confidence:
            lift = conf / item_support_dict[rhs]
            conv_a = (1- item_support_dict[rhs])
            conv_b = (1 - conf)
            if conv_b == 0:
              conv = "infinity"
            else:
              conv = conv_a/conv_b
            rules_info = lhs, rhs, conf, lift,conv, item_support_dict[freq_set]
            rules.append(rules_info)
            right_hand_side.append(rhs)
            
    return rules, right_hand_side


def generateRules(data,min_support, min_confidence):
    records = np.array(data)
    freq_items, item_support_dict,freq_item_support = aprioriFunc(records, min_support)
    association_rules= create_rules(freq_items, item_support_dict, min_confidence)
    #len_right = create_rules(freq_items, item_support_dict, min_confidence = 0.8)
    return association_rules,freq_item_support

def checkReduceRules(rules, data, min_support,min_confidence):
    while len(rules) > 5:                           
        min_support = min_support + 0.025
        rules,freq_item_support = generateRules(data, min_support, min_confidence)
        print(len(rules),min_support)

        if min_support >= 0.85 and len(rules) > 5:
            min_confidence = min_confidence +0.01
            rules,freq_item_support = generateRules(data, min_support, min_confidence)
            print("kondisi1 ",len(rules),min_support)

            if len(rules) <= 5 or min_support >=0.85:
                print("kondisi2",len(rules),min_support)
                break;

            if min_support >=0.85 and min_confidence >0.99 and len(rules) > 5:
                print("kondisi3",len(rules),min_support)
                break;
    
    return rules, min_support,min_confidence

def checkIncreaseRules(rules,data,min_support,min_confidence):
    while len(rules) == 0:                           
        min_support = min_support - 0.025
        rules,freq_item_support = generateRules(data, min_support, min_confidence)
        print(len(rules),min_support)

        if min_support <= 0.3 and len(rules) == 0:
            min_confidence = min_confidence - 0.01
            rules,freq_item_support = generateRules(data, min_support, min_confidence)
            print("kondisi1 ",len(rules),min_support)

            if len(rules) > 0 or min_support <=0.3:
                print("kondisi2",len(rules),min_support)
                break;

            if min_support <=0.85 and min_confidence <0.8 and len(rules) == 0:
                print("kondisi3",len(rules),min_support)
                break;
    
    return rules, min_support,min_confidence


                    