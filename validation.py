from __future__ import print_function
import sys
import imaplib
import getpass
import email
import email.header
import datetime
import os
import json
import csv
import hone
import ast
import pymongo
import gspread

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from jsonschema import validate
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder

EMAIL_ACCOUNT = "nslsii.provenance@gmail.com"
PASSWORD = ""

# Use 'INBOX' to read inbox.  Note that whatever folder is specified,
# after successfully running this script all emails in that folder
# will be marked as read.

EMAIL_FOLDER = "INBOX"
split_dict_list = []

# splitting_dict splits fields that have multiple components into arrays.
def splitting_dict(dicts):
    for d in dicts:
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
                                split_dict[key][new_key][next_key] = next_value.split(
                                    ";"
                                )
                            else:
                                split_dict[key][new_key][next_key] = next_value
                    else:
                        split_dict[key][new_key] = new_value
            else:
                split_dict[key] = value
    split_dict_list.append(split_dict)


# clear_spreadsheet clears the spreadsheet of all values (only keeping key names) using Google Sheets APIs
def clear_spreadsheet(spreadsheet_id):
    SHEETS_SCOPES = ['https://spreadsheets.google.com/feeds', 'http://www.googleapis.com/auth/drive']
    sheets_store = file.Storage("sheets_credentials.json")
    sheets_creds = sheets_store.get()
    if not sheets_creds or sheets_creds.invalid:
        sheets_flow = client.flow_from_clientsecrets("sheets_client_secret.json", SHEETS_SCOPES)
        sheets_creds = tools.tun_flow(sheets_flow, sheets_store)
    SHEETS_DRIVE = discovery.build("sheets", "v4", http=sheets_creds.authorize(Http()))
    gc = gspread.authorize(sheets_creds)
    spreadsheet = gc.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    worksheet.resize(rows=1)
    worksheet.resize(rows=30)
    print("Spreadsheet cleared!")

# schema_checker downloads the spreadsheet, converts it to json format, and checks if it is valid
# if valid, it then uploads to MongoDB and prints the resulting ID number for each sample uploaded
def schema_checker(google_file):
    if google_file:
        fn = (
            "%s.csv" % os.path.splitext(files[0]["name"].replace(" ", "_"))[0]
        )  # rename file with underscores
        print('Exporting "%s" as "%s"... ' % (files[0]["name"], fn), end="")
        data = DRIVE.files().export(fileId=files[0]["id"], mimeType=DST_MIMETYPE).execute()
        if data:
            with open(fn, "wb") as f:
                f.write(data)
            print("DONE")  # done exporting as csv file
            Hone = hone.Hone()  # convert csv file to nested json format, result is a list
            schema = Hone.get_schema(fn)
            result = Hone.convert(fn)
            splitting_dict(result)
            # since result is a list, iterate validation over each item:
            number = 0
            for data in split_dict_list:
                number += 1
                with open("materials.json", "r") as file:
                    loaded_schema = file.read()
                    validation_schema = ast.literal_eval(loaded_schema)
                validate(data, validation_schema)
                print('Sample %s validation complete!' % number) # prints only if no error occurs during validation step
                doc_id = coll.insert_one(data).inserted_id # insert validated schema into MongoDB
                print('The ID for this document is: ', doc_id)
                clear_spreadsheet(FILEID) # spreadsheet is only cleared if doc SUCCESSFULLY uploads to MongoDB
        else:
            print("ERROR: could not download file")
    else:
        print("ERROR: file not found")

# process_mailbox checks gmail for emails that are sent when new responses are submitted into the Google Form
# if such emails exist in its inbox, then it runs schema_checker
# if schema_checker is successful, it archives the email, removing it from the inbox
def process_mailbox(M):
    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        print("No messages found!")
        return

    for num in data[0].split():
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            print("ERROR getting message", num)
            return

        msg = email.message_from_bytes(data[0][1])
        hdr = email.header.make_header(email.header.decode_header(msg['Subject']))
        subject = str(hdr)
        if subject == 'New form response notification':
            print('New response found.')
            schema_checker(files)
            M.store(num, '+FLAGS', '\\Deleted')
        else:
            print('No new responses.')
    M.expunge()

# must be able to connect to MongoDB before running
# ssh must be set up to work
client = MongoClient(host="localhost", port=9876)
db = client["samples"]
coll = db["test"]

try:
    db.command("serverStatus")
except Exception as e: print(e)
else:
    print("You are connected to MongoDB!")

# need to download spreadsheet as a csv file using Google APIs
# Google APIs must be setup with computer running code to work, see Google Drive Quickstart for help

SCOPES = "https://www.googleapis.com/auth/drive.readonly"
store = file.Storage("storage.json")
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets("client_secret.json", SCOPES)
    creds = tools.run_flow(flow, store)
DRIVE = discovery.build("drive", "v3", http=creds.authorize(Http()))

FILENAME = str(input("Please enter filename: "))
FILEID = str(input("Please enter file ID: "))
SRC_MIMETYPE = "application/vnd.google-apps.spreadsheet"  # source file type
DST_MIMETYPE = "text/csv"  # exported file type

files = (
    DRIVE.files()
    .list(
        q='name="%s" and mimeType="%s"' % (FILENAME, SRC_MIMETYPE),
        orderBy="modifiedTime desc,name",
    )
    .execute()
    .get("files", [])
)

M = imaplib.IMAP4_SSL('imap.gmail.com')

try:
    rv, data = M.login(EMAIL_ACCOUNT, PASSWORD)
except imaplib.IMAP4.error:
    print ("LOGIN FAILED!")
    sys.exit(1)

rv, data = M.select(EMAIL_FOLDER)
if rv == 'OK':
    process_mailbox(M)
    M.close()
else:
    print("ERROR: Unable to open mailbox ", rv)

M.logout()
