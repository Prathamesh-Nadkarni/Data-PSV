import json
import csv
import os
def read_json_file():
    try:
        json_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'json', 'users_data.json')
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None


def read_sales_csv_file():
    try:
        csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'csv', 'ProductData.csv')
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
        return data
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
    

def read_social_media_csv_file():
    try:
        csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'csv', 'SocialMediaData.csv')
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
        return data
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
    



# Data Source https://www.kaggle.com/datasets/shreyanshverma27/online-sales-dataset-popular-marketplace-data?resource=download