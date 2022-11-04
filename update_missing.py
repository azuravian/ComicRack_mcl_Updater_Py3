#!/usr/bin/env python

"""
    Ver 2.0
    
    Overview:
    
    This script grabs the newest issues from ComicVine and 'appends' them to the
    missing.mcl file contents.
    
    usage:
    python update_missing.py <in_file> <out_file> <api_key> <start_date> <end_date>
    
        in_file:    missing.mcl (i.e., your most recent version)
        out_file:    missing_<date> (or w/e you want to name it) 
        api_key:    provided by ComicVine
        start_date:    the date the mcl file is synched with (YYYY-MM-DD)
        end_date:    today's date (YYYY-MM-DD)
    
    e.g.,
    python update_missing.py missing.mcl missing_20170917.mcl API_KEY 2017-09-11 2017-09-17
    
    Technical stuff:
    
    The mcl file format contains a header followed by a list of volumes with 
    their respective issues/numbers.
    
        Missing;<date_of_last_update>
        <volume_id>;list of <issue_id>;list of <issue_num>
        <volume_id>;list of <issue_id>;list of <issue_num>
        ...
        <volume_id>;list of <issue_id>;list of <issue_num>
    
    The lists are comma delimited.  Commas followed immediately by a space are 
    not considered a delimiter.  Some issues are numbered like "v. 1, no. 01".
    If there is a space in the list of issue numbers, the entire list is 
    wrapped in double quotes.
    
    Note: There is one volume (id: 77901) that has an issue number "1,5".  This
    can potentially wreak some havoc if not treated carefully.    
"""

import requests
import sys
import os

if len(sys.argv) < 4 :
    print("usage: python update_missing.py <api_key> <start_date> <end_date>")
    exit()

api_key = str(sys.argv[1])         # ComicVine API key
start_date = str(sys.argv[2])     # start date range to search for new issues
end_date = str(sys.argv[3])        # end date range to search for new issues
in_file = str(f"{sys.argv[2]}_latest.mcl")
out_file = str(f"{sys.argv[3]}_latest.mcl")

comiclist = open(in_file, "r")
issues_number = {}
issues_volume = {}
skip_header = True
cont = 0

print("Reading in current database")
for line in comiclist:
    if skip_header:
        skip_header = False
        continue
    
    line_split = line.replace("\n","").split(";")
    volume_id = int(line_split[0])
    
    if (line_split[1][0] == '"') and (line_split[1][len(line_split[1])] == '"'):
        line_split = line_split[1:-1]
    
    issue_split = line_split[1].split(",")
    num_split = line_split[2].split(",")
    
    for i in range(0,len(issue_split)):
        if int(issue_split[i]) in issues_number:
            cont += 1
        issues_number[int(issue_split[i])] = num_split[i]
        issues_volume[int(issue_split[i])] = volume_id

comiclist.close()

print("Querying ComicVine for new issues")
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
new_comics_cont = 0
old_comics_cont = 0
updated_comics_cont = 0
deleted_comics_cont = 0
comic_skip_cont = 0
offset = 0
max = 100
limit = 100
skip = 0
retry = 0
ErrorIds = ""
non_retrieved_comics = issues_number.copy()
FindingError = False

while offset < max:
    try:
        request_url = f"https://comicvine.gamespot.com/api/issues/?api_key={api_key}&limit={str(limit)}&format=json&offset={str(offset)}&field_list=id,issue_number,volume&filter=date_last_updated:{start_date}|{end_date}&sort=id"
        
        '''print request_url'''
        r = requests.get(request_url, headers=headers)
        json_obj = r.json()

        max = json_obj['number_of_total_results']
       
        print(str(min(offset,max)) + "/" + str(max) + " Since " + start_date)
        
        for i in json_obj['results']:
            volume_id = i['volume']['id']
            issue_id = i['id']
            num = i['issue_number'].replace(",",".&@1").replace(";",".&@2").replace("\n","").replace("\r","")
            
            if issue_id not in issues_number:
                new_comics_cont += 1
                issues_number[issue_id] = num
                issues_volume[issue_id] = volume_id
            else:
                del non_retrieved_comics[issue_id]
                old_comics_cont += 1
                if issues_number[issue_id] != num or issues_volume[issue_id] != volume_id:
                    updated_comics_cont += 1
                    issues_number[issue_id] = num
                    issues_volume[issue_id] = volume_id

        offset += limit + skip
        
        FindingError = False

        if skip == 1:
            print("Comic with error found, id= " + str(issue_id+1))
            ErrorIds += ";"+ str(issue_id+1)
            comic_skip_cont += 1
            print("Continue loading comics now...")
            FindingError = True
        
        skip = 0
        limit = 100
        retry = 0
        
    except:
        if retry < 4 and not FindingError:
            print("Error. Trying Again...")
            retry += 1
        else:
            
            if not FindingError:
            
                print("Finding Error in comic list: " + str(100-limit) + "%")
                skip = 1
                limit -= 1
            
            if limit == 0 or FindingError:
                print("Comic with error found, id= " + str(issue_id+offset))
                FindingError = True
                limit = 1
                offset += 1
                comic_skip_cont += 1
                ErrorIds += ";"+ str(issue_id+offset)

comics = {}
for issue_id in issues_number.keys():
    if issues_volume[issue_id] not in comics:
        comics[issues_volume[issue_id]] = {}
    comics[issues_volume[issue_id]][issue_id]=issues_number[issue_id]

print("Writing missings to file")

deleted_file = open("Deleted_Comics.txt", "wb")

for issue_id in non_retrieved_comics.keys():
    deleted_file.write(bytes(str(issue_id)+"\n", "utf-8"))
    deleted_comics_cont += 1

deleted_file.close()
    
print("Writing database to file")

outfile = open(out_file,"wb")
outfile.write(bytes("Missing;" + end_date + "\n", 'utf-8'))

for volume_id in sorted(comics):
    issues = ""
    nums = ""
    for issue_id in sorted(comics[volume_id]):
        issues += str(issue_id) + ","
        nums += comics[volume_id][issue_id] + ","
    issues = issues[:-1]
    outfile.write(bytes(str(volume_id) + ";" + issues + ";" + nums + "\n", 'utf-8'))
    
outfile.close()
os.rename(in_file,in_file.replace('latest', 'missing'))

print("Done! " + str(new_comics_cont) + " comics added to database! (" + str(comic_skip_cont)+ " skipped and " + str(old_comics_cont) + " comics already in database)")
print(str(deleted_comics_cont) + " comics in databased not retrieved in this round.")
print(str(updated_comics_cont) + " comics updated in database.")
print("Ids with error in server: " + ErrorIds[1:])
print(cont)
input("Press Enter to continue...")