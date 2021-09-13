import copy
import json

def save_json_to_file(fileName, data):
    with open(fileName, 'w') as f:
        f.write(json.dumps(data, indent=4))

def filter_by_open(data):
    # create a deep copy of data to prevent a change in the objects size during iteration
    data_open_spots = copy.deepcopy(data)

    # iterate over the data and remove all of the positions with 0 available spots
    for (key_fair, fair) in data.items():
        print(key_fair)
        for (key_company, company) in fair.items():
            print(key_company)
            if (isinstance(company, str)):
                del data_open_spots[key_fair][key_company]
                continue
            for (key_position, position) in company.items():
                print(key_position)
                if (position['Spots Open'] == 0):
                    del data_open_spots[key_fair][key_company][key_position]

    # remove the companies with empty directories (no positions)
    for (key_fair, fair) in data_open_spots.items():
        data_open_spots[key_fair] = {i:j for i,j in fair.items() if j != {}}

    return data_open_spots
                