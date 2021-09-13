from scrapper import scrape_fairs
from utils import filter_by_open, save_json_to_file

fair_list = [
    {
        'url': "https://app.careerfairplus.com/ncsu_nc/fair/3116",
        'filter_by_major': 'Computer Science'
    },
    {
        'url': "https://app.careerfairplus.com/ncsu_nc/fair/3720",
        'filter_by_major': ''
    },
]


extracted_data = scrape_fairs(fair_list)

save_json_to_file('unparsed_list.json', extracted_data)


open_spots_dict = filter_by_open(extracted_data)

save_json_to_file('filtered_by_open.json', open_spots_dict)






