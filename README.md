# ComicRack_mcl_Updater_Py3
Script using Python 3+ to update mcl files used by ComicRack's Find Missing Issues Offline plugin

The command for running the script is 
python update_missing.py <apikey> <start date> <end date>

Name your current mcl file as ########_latest.mcl (where ######## represents the date in whatever format you prefer).  Use the same date format when running the script and it will detect that file and output the new one using the same format.  The new file will be appended with _latest.mcl, while the existing one will be renamed to _missing.mcl.
  
Future uses will follow suit, so you always have all prior mcl files named ########_missing.mcl and the lastest named ########_latest.mcl.
