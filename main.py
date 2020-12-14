import requests
import pandas as pd
import pandas.io.json
import json
import ast

city_name = '深圳市'
# city_name = '成都市'
# city_name = '北京市'
line_number = 1

line_number_name = str(line_number) + '号线'
lines_list = "" 
# anyone using this code needs to get their own keys from amap.com
api_key_web_service = open('../api_key_web_service.txt', encoding='utf-8').read() # Web Service (Web服务)
api_key_web_end = open('../api_key_web_end.txt', encoding='utf-8').read()         # Web End (Web端)




def getEnglishCityName():

    URL = 'https://restapi.amap.com/v3/place/text?'
    PARAMS = {  
                'keywords': city_name,
                'output':'json',
                'offset':'1',
                'page':'1',
                'key': api_key_web_service,
                'citylimit':'true',
                'language':'en'
                # 'extensions':'all',
                }

    rEn = requests.get(url = URL, params = PARAMS)
    dataEn = rEn.json()
    city_name_en = str(dataEn['pois'][0]['name']).split(" ")[0]
    # pp = pprint.PrettyPrinter(indent=1)
    # pp.pprint(dataEn)
    # print(dataEn['pois'][0]['polyline'])
    
    return city_name_en

def getEnglishName(location):

    URL = 'https://restapi.amap.com/v3/place/text?'
    PARAMS = {  
                # 'keywords': line_number_name, 
                'location': location, 
                'city': city_name,
                'output':'json',
                'offset':'1',
                'page':'1',
                'key': api_key_web_service,
                'citylimit':'true',
                'language':'en',
                'types': '150500'
                # 'extensions':'all',
                }

    rEn = requests.get(url = URL, params = PARAMS)
    eng_name = rEn.json()
    
    # pp = pprint.PrettyPrinter(indent=1)
    # pp.pprint(dataEn)
    # print(dataEn['pois'][0]['polyline'])
    
    return str(eng_name['pois'][0]['name']).split('(')[0]

def getEnglishNameBatches(location_list):
    station_names_en = []

    while len(location_list):
        len_of_locations = 20 if len(location_list)>20 else len(location_list)
        print("len of locations: " + str(len_of_locations))
        station_names_en += getOneBatch(location_list, len_of_locations)
        location_list = location_list[len_of_locations:] # update the array to only include the last data points
        len_of_locations = 0 # update the length to zero
        
    print(station_names_en)
    return station_names_en

def getOneBatch(location_list, len_of_locations):
    ops_url_list = ['' for i in range(len_of_locations)]
    station_names_en = ['' for i in range(len_of_locations)]
    main_query = '/v3/place/text?city=' + city_name + '&output=json&offset=1&page=1&key=' + api_key_web_service + '&citylimit=true&language=en&types=150500&location='

    BURL = 'https://restapi.amap.com/v3/batch?key=' + api_key_web_service 
    BPARAMS = '{"ops": ['
    for x in range(len_of_locations):
        ops_url_list[x] = main_query + location_list[x]
        BPARAMS += '{"url": "' + ops_url_list[x] + '"}'
        BPARAMS += ']}' if (x == len_of_locations-1) else ','

    body = json.loads(BPARAMS)
    url = 'https://restapi.amap.com/v3/batch'
    params= {'key':api_key_web_service}
    responseBatchEn = requests.post(url,params=params,json=body)
    dataEn = responseBatchEn.json()

    for x in range(len_of_locations):
        station_names_en[x] = str(dataEn[x]['body']['pois'][0]['name']).split('(')[0]

    return station_names_en

# select_line specifies which of the returned results to use. 
# Sometimes the first result is not the correct one, or it's not the only one*
# *(in the case of a line that has a split)
# The default value is the first result "0"

def getOneLine(line_num, select_line = 0):
    busline_number = select_line
    URL_zh = 'http://restapi.amap.com/v3/bus/linename?' 
    PARAMS_zh = {'s':'rsv3',
                'key': api_key_web_end,
                'output':'json',
                'pageIndex':'1',
                'city': city_name,
                'offset':'10',
                # 'keywords':'1号线|3号线|7号线|9号线'
                'keywords': line_num,
                # 'keywords':'地铁',
                'extensions':'all'
                }
    rZh = requests.get(url = URL_zh, params = PARAMS_zh)
    dataZh = rZh.json()

    number_of_stations = len(dataZh['buslines'][busline_number]['busstops'])
    print(number_of_stations)
    station_names_zh = ["" for i in range(number_of_stations)]
    station_coords_zh = ["" for i in range(number_of_stations)]
    for x in range(number_of_stations):
        station_names_zh[x] = dataZh['buslines'][busline_number]['busstops'][x]['name']
        station_coords_zh[x] = dataZh['buslines'][busline_number]['busstops'][x]['location']


    list_of_eng_stations = getEnglishNameBatches(station_coords_zh)
    print("Chinese/English names")
    stations_en = '['
    for x in range(len(list_of_eng_stations)):    
    # for x in range(3):    
        print(station_names_zh[x] + " is " + str(list_of_eng_stations[x]))
        stations_en += '[\"'
        stations_en += list_of_eng_stations[x] + '\",\"' 
        stations_en += station_names_zh[x] + '\",' 
        stations_en += str(float(get_lat(station_coords_zh[x]))) + ','  
        stations_en += str(float(get_lon(station_coords_zh[x]))) + '],'
    stations_en += ']'
    print(stations_en)
    stations_en = ast.literal_eval(stations_en)
   
    subway_data = pandas.io.json.json_normalize(data=dataZh['buslines'],
                                            errors='ignore',
                                            record_prefix='_')
    df = pd.DataFrame(subway_data)
 
    # create a new dataframe with only the columns listed as arguments
    # df_essentials = df[['name','uicolor', 'polyline']]
    coords_list = [[0
                    for i in range(len(df['polyline']))] 
                    for j in range(100)]


    for x in range(len(df['polyline'])):
        coords_list[x] = str(df['polyline'][x]).split(';')

    coords_list_float = [0
                    for i in range(len(coords_list[busline_number]))]

    for i in range(len(coords_list[busline_number])):
        coords_list_float[i] = [float(get_lat(coords_list[busline_number][i])), float(get_lon(coords_list[busline_number][i]))]
    

    line_name = str(df['name'].iloc[0])
    line_colour = str(df['uicolor'].iloc[0])
    start_time =  str(df['start_time'].iloc[0])
    end_time =  str(df['end_time'].iloc[0])

    return [coords_list_float, line_colour, stations_en]
    

def getZhongWen():
    line_num = 1
    print()
    # Chengdu
    # line_lists = [getOneLine(1), getOneLine(2), getOneLine(3), getOneLine(4), getOneLine(7), getOneLine(10)]
    # line_lists = [getOneLine(1), getOneLine(1, 2), getOneLine(2), getOneLine(3), getOneLine(4), getOneLine(5), getOneLine(7), getOneLine(10), getOneLine(18)]
    # line_lists = [getOneLine(1, 2)]
    # Shenzhen
    line_lists = [getOneLine(1), getOneLine(2), getOneLine(3), getOneLine(4),getOneLine(5),getOneLine(6,2), getOneLine(7),getOneLine(9), getOneLine(10),getOneLine(11)]
    # line_lists = [getOneLine(6,2)]
    #Beijing
    # line_lists = [getOneLine(1), getOneLine(2), getOneLine(3), getOneLine(4),getOneLine(5), getOneLine(7),getOneLine(9), getOneLine(11)]
    #Guangzhou
    # line_lists = [getOneLine(1), getOneLine(2), getOneLine(3), getOneLine(4),getOneLine(5), getOneLine(7),getOneLine(9), getOneLine(11)]
    #Shanghai
    # line_lists = [getOneLine(6), getOneLine(10)]
    
    lines = [line_lists[0][0]]
    lineColors = ['#'+ line_lists[0][1]]
    stations = [line_lists[0][2]]

    for x in range(len(line_lists)-1):
        x = x +  1
        lines.append(line_lists[x][0])
        lineColors.append('#' + line_lists[x][1])
        stations.append(line_lists[x][2])

    icon = "./markers/"+ getEnglishCityName() +".png"
    
    json_dict = {
        "city": city_name,
        "lines": lines,
        "lineColors": lineColors,
        "stations": stations,
        "icon": icon
    }
    # convert to standardised JSON
    # don't change to ascii (which doesn't have Chinese character support)
    json_output = json.dumps(json_dict, ensure_ascii=False) #, indent=4)  
    create_file(json_output)
    
def create_file(json_output):
    filename = city_name + '_output_lines.json'
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(json_output)
    print('---   end of csv file')

def get_lat(coords):
    return str(coords).split(',')[0]

def get_lon(coords):
    return str(coords).split(',')[1]

# getEnglish()
print('starting')
getZhongWen()