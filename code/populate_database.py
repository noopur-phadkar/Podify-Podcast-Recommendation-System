import json
import os
from access_database import DatabaseConnection
from sentiment_analysis import SentimentAnalysis
import xml.etree.ElementTree as et


class Populate_Database:

    def __init__(self):
        # Filepaths of directories containing Podcast Transcripts and Metadata
        self.transcript_directory = "/Users/noopurparagphadkar/Library/CloudStorage/OneDrive-rit.edu/Capstone/spotify-data/6"
        self.metadata_directory = "/Users/noopurparagphadkar/Desktop/spotify-metadata/6"
        self.processed_title = "this_title_has_been_processed"  # Strings used to mark processed metadata
        self.invalid_xml = "no_metadata_is_available"  # Strings used to mark invalid metadata
        self.database_connector = DatabaseConnection("capstone", "transcripts")
        self.sentiment_analysis = SentimentAnalysis()

    def insert_into_database(self, transcript: str, title: str, authors: str):
        """
        This function inserts a podcast's title, author, entities and their sentiments into mongodb
        :param transcript: string containing the transcript
        :param title: string containing the title of podcast
        :param authors: list containing authors of podcast
        :return: None
        """
        if not isinstance(transcript, str):  # Print if transcript is processed incorrectly
            print("Transcript: " + transcript)
        entry = {"title": title,  # Dictionary to store data
                 "author": authors,
                 "entities": self.sentiment_analysis.get_sentiment_for_entities(transcript),
                 "genre": self.sentiment_analysis.genre_generation(transcript)}
        self.database_connector.insert_podcast_into_database(
            entry)  # Call function to insert data into monogodb collection

    def extract_transcript(self, data: dict):
        """
        This function extracts the transcript as a single string from the json
        :param data: json containing transcript
        :return: string containing transcript
        """
        transcript = ""  # To store transcript
        # This loop goes through the json file containing the transcript
        for alternatives in data["results"]:
            for alternative in alternatives["alternatives"]:
                if len(alternative) > 0:
                    if 'transcript' in alternative.keys() and isinstance(alternative["transcript"], str):
                        transcript += alternative["transcript"]
                else:
                    if isinstance(alternative, str):
                        transcript += print(alternative)
        return transcript.strip()

    def get_title_author(self, filepath: str):
        """
        This function extracts the podcast title and author from the respective rss folder
        :return: (string, string) containing title as string and authors in list format
        """
        try:
            tree = et.parse(filepath)  # Read metadata stored in xml format
            root = tree.getroot()
            title, authors = "", ""  # To store title and authors of podcast
            found = False
            # This loop goes through the xml tree and extracts the title ana author of the podcast
            for episode in root[0].iter("item"):
                if episode.find("title").text != self.processed_title:
                    found = True
                    title = episode.find("title").text
                    authors = episode.find('{http://purl.org/dc/elements/1.1/}creator').text.replace(" and ",
                                                                                                     ",").strip()
                    episode.find("title").text = self.processed_title  # Change title to mark it as processed
                    break
            if found:
                tree.write(filepath)
                return title, authors
            else:
                return self.invalid_xml, self.invalid_xml
        except Exception as e:  # Return a string if xml metadata is incorrect
            print(e)
            return self.invalid_xml, self.invalid_xml

    def main(self):
        """
        This function loops through all the files in the root directory to access all the podcast data
        loc = os.path.join(subdir, file).replace(transcript_dir, "").replace(".json", ".xml")
        """
        f1 = open('not_read.txt', 'a+')
        for subdir, dirs, files in os.walk(self.transcript_directory):
            for file in files:
                if file.endswith('.json'):
                    with open(os.path.join(subdir, file), "r+") as f:
                        # title, authors = get_title_author(podcast_dir + subdir[-34:] + ".xml")
                        title, authors = self.get_title_author(self.metadata_directory + subdir[-30:] + ".xml")
                        if title == self.invalid_xml:
                            continue  # Skip podcast if no metadata given
                        data = json.load(f)
                        transcript = self.extract_transcript(data)
                        try:
                            self.insert_into_database(transcript, title, authors)
                        except:
                            f1.write(os.path.join(subdir, file) + '\n')
        f1.close()


if __name__ == '__main__':
    populate_database = Populate_Database()
    populate_database.main()
