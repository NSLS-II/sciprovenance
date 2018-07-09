from __future__ import print_function
import os
import json
import csv
import hone
import ast
import pymongo
import pprint

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from jsonschema import validate
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder

# must have ssh setup with MongoDB in order to connect

print("Connecting to MongoDB...")

client = MongoClient(host="localhost", port=9876)
db = client["samples"]
coll = db["test"]

try:
    db.command("serverStatus")
except Exception as e: print(e)
else:
    print("You are connected!")

# need to download spreadsheet as a csv file using Google APIs
# part of this code was taken from wescpy.blogspot.com
# must have Google APIs set up with Google account, see Google Drive APIs Quickstart for help

SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

FILENAME = str(input("Please enter filename: "))
SRC_MIMETYPE = 'application/vnd.google-apps.spreadsheet' # source file type
DST_MIMETYPE = 'text/csv' # exported file type

# finds file in Google Drive
files = (
    DRIVE.files()
    .list(
        q='name="%s" and mimeType="%s"' % (FILENAME, SRC_MIMETYPE),
        orderBy='modifiedTime desc,name'
    )
    .execute()
    .get('files', [])
)

if files: # if file was found
    fn = (
        '%s.csv' % os.path.splitext(files[0]['name'].replace(' ', '_'))[0]
    ) # create csv file with underscores
    print('Exporting "%s" as "%s"... ' % (files[0]['name'], fn), end='')
    data = DRIVE.files().export(fileId=files[0]['id'], mimeType=DST_MIMETYPE).execute()
    if data:
        with open(fn, "wb") as f:
            f.write(data)
        print("DONE")  # done exporting as csv file
        Hone = hone.Hone()  # convert csv file to nested json format, result is a list
        schema = Hone.get_schema(fn)
        result = Hone.convert(fn)
        split_dict_list = [] # this is where the final list of dictionaries is inserted
        # need to split strings that contain multiple values separated with ';' to create arrays
        # need to rename key names to contain underscores instead of dashes
        # since there is multiple nestings in the schema, for loops and if statements are also nested
        for d in result:
            split_dict = {}
            for key, value in d.items():
                key = key.replace("-", "_")
                if isinstance(value, str) == True and ";" in value:
                    split_dict[key] = value.split(";")
                elif isinstance(value, dict) == True:
                    split_dict[key] = {}
                    for new_key, new_value in value.items():
                        new_key = new_key.replace("-", "_")
                        if isinstance(new_value, str) == True and ";" in new_value:
                            split_dict[key][new_key] = new_value.split(";")
                        elif isinstance(new_value, dict) == True:
                            split_dict[key][new_key] = {}
                            for next_key, next_value in new_value.items():
                                next_key = next_key.replace("-", "_")
                                if (
                                    isinstance(next_value, str) == True
                                    and ";" in next_value
                                ):
                                    split_dict[key][new_key][
                                        next_key
                                    ] = next_value.split(";")
                                else:
                                    split_dict[key][new_key][next_key] = next_value
                        else:
                            split_dict[key][new_key] = new_value
                else:
                    split_dict[key] = value
            split_dict_list.append(split_dict)
        # since result is a list, iterate validation over each item:
        number = 0
        for data in split_dict_list:
            number += 1
            with open("materials.json", "r") as file:
                loaded_schema = file.read()
                validation_schema = ast.literal_eval(loaded_schema)
                validate(data, validation_schema)
                print('Sample %s validation complete!' % number) # prints only if no error occurs on validation step
                doc_id = coll.insert_one(data).inserted_id # insert validated schema into MongoDB
                print('The ID for this document is: ', doc_id)
    else:
        print("ERROR (could not download file)")
else:
    print("ERROR: file not found")
