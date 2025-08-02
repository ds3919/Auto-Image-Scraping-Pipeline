import csv
import pandas as pd
import requests
import os
from sys import argv
output_folder = argv[2]
if (os.path.exists(output_folder)) == False:
    os.makedirs(output_folder)

# Read the CSV
df = pd.read_csv(argv[1], encoding='latin1')

print(df.head)

words = df["word"]
categories = df["categorization"]
filenames = []
failedfiles = []


# Seperates images based on their category (T or F)
j = 1
for i in range(len(words)):
    if categories[i]:
        filenames.append(words[i])
    else:
        filenames.append(None)
        failedfiles.append(words[i])
        
for file in filenames:
    print(file)


# Drops all rows with any empty values
df['filename'] = filenames
df_cleaned = df.dropna(subset=["filename"])

df_cleaned.reset_index()
print(df_cleaned.head)


print(df_cleaned.columns)

# Iterates through rows and downloads images off of the url and assigns it a filename in the currect format
# Make sure to change suffix "en" to whatever suffix you prefer based on any characteristic
for index, row in df_cleaned.iterrows():
    url = row['urls']
    filename = row['filename']
    try:
        response = requests.get(url, stream = True)
        response.raise_for_status()

        file_path = os.path.join(output_folder, (filename + f"_en{index}.jpg"))
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Downloaded: {filename}_en{index}.jpg")
    
    except Exception as e:
        print(f"Failed to download {url}: {e}")
