import nltk
import openai
from flair.nn import Classifier
from flair.splitter import SegtokSentenceSplitter
from openai.error import RateLimitError
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import time


class SentimentAnalysis:
    def __init__(self):
        # GPT_MODEL = "gpt-3.5-turbo"           # model's maximum context length is 4097 tokens
        self.GPT_MODEL = "gpt-3.5-turbo-16k"  # model's maximum context length is 16384 tokens
        # GPT_MODEL = "babbage-002"          # model's maximum context length is 16384 tokens
        self.splitter = SegtokSentenceSplitter()  # initialize sentence splitter
        self.tagger = Classifier.load('ner')  # load the NER tagger
        # self.tagger = Classifier.load('flair/ner-english-ontonotes-large')
        nltk.download('punkt')
        self.tokenizer = AutoTokenizer.from_pretrained("fabiochiu/t5-base-tag-generation")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("fabiochiu/t5-base-tag-generation")

    def genre_generation(self, transcript):
        """
        This function generates and prints the genre of the transcript given.
        :param transcript: Transcript of a podcast. This is used to generate the genre.
        :return: list containing tags or genres
        """
        inputs = self.tokenizer([transcript], max_length=512, truncation=True, return_tensors="pt")
        output = self.model.generate(**inputs, num_beams=8, do_sample=True, min_length=10, max_length=64)
        decoded_output = self.tokenizer.batch_decode(output, skip_special_tokens=True)[0]
        tags = list(set(decoded_output.strip().split(", ")))
        return tags

    def process_entities(self, sentences: list):
        """
        This function takes a list of sentences as input and processes them to return a list of entities
        :param sentences: list containing sentences of type  flair.data.Sentence
        :return:    list of all tags identified by the flair transformer
        """
        entities = set()
        for sentence in sentences:
            if str(sentence).__contains__("→"):
                for entity in str(sentence).split(" → ")[1][1:-1].split(", "):
                    entities.add(entity.split("/")[0][1:-1])
        return list(entities)

    def entity_identification(self, transcript):
        """
        This function takes in a transcript as input and uses the flair transformer to identify all the entities in the
        transcript.
        :param transcript:  string containing the transcript :return:    list of all th entities
        """
        sentences = self.splitter.split(transcript)  # use splitter to split text into list of sentences
        self.tagger.predict(sentences)  # run NER over sentence
        return self.process_entities(sentences)

    def make_open_api_call(self, query: str):
        """
        This function is used to make the OpenAPI call
        :param query: Query to make API call
        :return: json containing the API response
        """

        response = openai.ChatCompletion.create(
            messages=[
                {'role': 'user', 'content': query},
            ],
            model=self.GPT_MODEL,
            temperature=0,
            request_timeout=60000
        )
        return response

    def extract_sentiments(self, sentiment_str):
        sentiments = {}
        lines = sentiment_str.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if line != '':
                entity = line.split(":")[1].strip()
                sentiment = lines[i + 1].split(":")[1].strip()
                sentiments[entity] = sentiment
                i += 3  # Increment by 3 to skip two lines after capturing an entity and its sentiment
            else:
                i += 1  # Increment by 1 if empty line
        return sentiments

    def open_api_sentiment_analysis(self, transcript: str, entities: list):
        """
        This function takes in the transcript and all the entities and prints out the sentiment for each entity.
        :param transcript: string containing teh transcript.
        :param entities: list of all the entities identified by teh flair transformer.
        :return: None
        """
        query = f"""Use the specified transcript to select the best word from the given list of words to describe the 
        sentiment for each of the entities in the entity list?
        
        Transcript: {transcript}
        
        Words: Positive, Negative, Neutral, Mixed
        
        Entities: {entities}
        
        Return a response in the following format:
        Entity:
        Sentiment:
        Entity:
        Sentiment:
        ...
        """

        try:
            response = self.make_open_api_call(query)
        except RateLimitError:
            time.sleep(2)
            response = self.make_open_api_call(query)  # TODO - put into a loop
        sentiment = response['choices'][0]['message']['content']
        return self.extract_sentiments(sentiment)

    def get_sentiment_for_entities(self, transcript: str):
        """
        This function takes transcript as input and prints the sentiment of all identified identities in it.
        :return: None
        """
        entities = self.entity_identification(transcript)  # function call to identifies all the entities in the transcript
        # return entities
        return self.open_api_sentiment_analysis(transcript, entities)    # function call to get sentiment of all entities


def main():
    sentiment_analysis = SentimentAnalysis()
    with open("test_transcript.txt", "r") as f:
        transcript = f.readline()
        entities = sentiment_analysis.entity_identification(transcript)
        print(sentiment_analysis.open_api_sentiment_analysis(transcript, entities))


if __name__ == '__main__':
    main()
