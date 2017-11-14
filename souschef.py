#!/usr/bin/env python
import os
import sys
sys.path.append(os.getcwd()) # Handle relative imports
from utils import data_writer, path_builder, downloader
from le_utils.constants import licenses, exercises, content_kinds, file_formats, format_presets, languages


""" Additional imports """
###########################################################
import logging
import csv
import re		# Read hyperlinks and titles from csv file, hacky solution
import string 	# To work around forward slashes in titles, see additional notes (1)

""" Run Constants"""
###########################################################

CHANNEL_NAME = "Better World Ed"              # Name of channel
CHANNEL_SOURCE_ID = "learningequality"      # Channel's unique id
CHANNEL_DOMAIN = "info@learningequality.org"					# Who is providing the content
CHANNEL_LANGUAGE = "en"		# Language of channel
CHANNEL_DESCRIPTION = None                                  # Description of the channel (optional)
CHANNEL_THUMBNAIL = None                                    # Local path or url to image file (optional)
PATH = path_builder.PathBuilder(channel_name=CHANNEL_NAME)  # Keeps track of path to write to csv
WRITE_TO_PATH = "{}{}{}.zip".format(os.path.dirname(os.path.realpath(__file__)), os.path.sep, CHANNEL_NAME) # Where to generate zip file


""" Additional Constants """
###########################################################
BASE_URL = 'https://www.betterworlded.org/try'

# Read csv file

# csv file name
filename = "bwe_overall_database.csv"

""" Main Scraping Method """
###########################################################
def scrape_source(writer):
	""" scrape_source: Scrapes channel page and writes to a DataWriter
        Args: writer (DataWriter): class that writes data to folder/spreadsheet structure
        Returns: None

        Better World Ed is organized with the following hierarchy:
            Grade Level (Folder) ***There may not be an assigned grade level*** (there should be 24 unassigned grade level rows), as of 11/11/2017
            |   Math Topic (Folder)  ***May come as a hyperlink***
			|   |   Specific Objective (Folder) ***May come as a hyperlink***
			|   |   |   Written Story (File) <- Google Drive or Google Docs, .pdf
			|   |   |   Video (File) <- Vimeo video file, .mp4
			|   |   |   Lesson Plan (File) <- Google Drive or Google Docs, .pdf


		Additional notes:

		1)
		There are some cases where we would want to remove forward slashes (/), from the titles of files or folders.
		This is because when trying to name a folder, the PATH variable and Datawriter will create a new folder, for example:
		the 120th record, row 4, has the hyperlink, "I Am Shantanu // Chai & Community". This will cause the Datawriter to
		add a folder, "I Am Shantanu", with a file inside named " Chai & Community", with a preceding whitespace, instead
		of a file "I am Shantanu // Chai & Community". The current workaround to this is to sanitize input to
		the Datawriter's add_file method, by replacing forward slashes ("/"), with pipes ("|").

		2)
		Updated downloader.py in utils to account for downloading from Google.

		3)
		The spreadsheet given to us was generated by the following:
		https://github.com/learningequality/sushi-chef-better-world-ed/pull/1
		Thus, the database appears as:
		+-------------------+------------+--------------------+---------------+-------+-------------+-----------+
		| Grade Level Range | Math Topic | Specific Objective | Written Story | Video | Lesson Plan | BWE Topic |
		+-------------------+------------+--------------------+---------------+-------+-------------+-----------+
		with the names of the columns appearing in the first row, meaning all records begin at row 2.
		At this time (11/10/2017), the "BWE Topic" column is not utilized. The columns are zero indexed,
		so column 0 corresponds to "Grade Level Range", and column 6 corresponds to "BWE Topic".

        Args: writer (Datawriter): class that writes data to folder/csv structure
		Returns: None
    """

	count = 0 # Temporary, to verify correct output

	with open(filename, 'r') as csvfile:
		# Creating csv reader object
		csvreader = csv.reader(csvfile)

		# Extracting each data row one by one
		for row in csvreader:
			if count == 0: # Skip the headers
				count += 1
				continue
			if count == 2: # Temporary, to ensure code works on the first few rows
				break

			# Some folders are named as hyperlinks
			gradeLevel = row[0]
			if gradeLevel == "":
				gradeLevel = "Other"

			# Setting the math topic and specific objective, as the database is
			# zero indexed, row[1] will correspond to the current row, column 1,
			# which is the title of the math topic. The specific objective is similar,
			# except it takes in the specific objective, at column 2.
			# Actual input will be sanitized with the try/except blocks immediately following.
			mathTopic = row[1]
			specificObjective = row[2]

			# There are records in which the math topic and specific objectives in the
			# database are given as hyperlinks, with the structure:
			# "=HYPERLINK("https://www.khanacademy.org/math/cc-fourth-grade-math/cc-4th-fractions-topic","Fractions")"
			# Thus, regular expressions are used to take in the correct title. See note 1 above.
			# TODO: Ask if there's anything we should be doing with the url.
			try:
				match = re.findall(r'\"(.+?)\"', row[1])
				mathTopic = match[1].replace('/', '|')
			except:
				mathTopic = row[1].replace('/', '|')
			try:
				match = re.findall(r'\"(.+?)\"', row[2])
				specificObjective = match[1].replace('/', '|')
			except:
				specificObjective = row[2].replace('/', '|')

			# Set the path and add folders
			PATH.set(gradeLevel, mathTopic, specificObjective)
			writer.add_folder(str(PATH), specificObjective)

			# Written story (3th column, zero indexed)
			try:
				matches = re.findall(r'\"(.+?)\"', row[3])
				title = matches[1].replace('/', '|')
				print ("Adding written story: " + matches[1])
				writer.add_file(str(PATH), title, matches[0], ext=".pdf", license=licenses.CC_BY, copyright_holder="betterworlded")
			except Exception as e:
				print ("Error in extracting written story link from: " + row[3], str(e))

			# Video (4th column, zero indexed)
			try:
				matches = re.findall(r'\"(.+?)\"', row[4])
				title = matches[1].replace('/', '|')
				print ("Adding video: " + title)
				print ("Video url: " + matches[0])
				file_path = writer.add_file(str(PATH), title, matches[0], ext=".mp4", license=licenses.CC_BY, copyright_holder="betterworlded")
			except:
				print ("Error in extracting video link from: " + row[4])

			# Lesson plan (5th column, zero indexed)
			try:
				matches = re.findall(r'\"(.+?)\"', row[5])
				title = matches[1].replace('/', '|')
				print ("Adding lesson plan: " + matches[1])
				writer.add_file(str(PATH), title, matches[0], ext=".pdf", license=licenses.CC_BY, copyright_holder="betterworlded")
			except:
				print ("Error in extracting lesson plan link from: " + row[5])

			count += 1

""" Helper Methods """
###########################################################


""" This code will run when the sous chef is called from the command line. """
if __name__ == '__main__':

    # Open a writer to generate files
    with data_writer.DataWriter(write_to_path=WRITE_TO_PATH) as writer:

        # Write channel details to spreadsheet
        thumbnail = writer.add_file(str(PATH), "Channel Thumbnail", CHANNEL_THUMBNAIL, write_data=False)
        writer.add_channel(CHANNEL_NAME, CHANNEL_SOURCE_ID, CHANNEL_DOMAIN, CHANNEL_LANGUAGE, description=CHANNEL_DESCRIPTION, thumbnail=thumbnail)

        # Scrape source content
        scrape_source(writer)

        sys.stdout.write("\n\nDONE: Zip created at {}\n".format(writer.write_to_path))
