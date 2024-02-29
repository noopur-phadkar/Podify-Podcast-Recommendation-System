from access_database import DatabaseConnection


class RetrievePodcasts:
    """
    This class is used to print a list of information of the top 5 similar podcasts calculated using weighted sum.
    """

    def __init__(self, title: str):
        self.top = 5
        self.database_connector = DatabaseConnection("capstone", "transcripts")
        self.podcast = self.database_connector.find_podcast_using_title(title)[0]
        self.recommended_podcasts = []

    def calculate_similarity(self, podcast_to_compare: dict):
        """
        This function is used to calculate the similarity between 2 podcasts.
        The list of priorities for finding similarity starting from the highest weighted property -
        1. occurrence of an entity with the same sentiment - 0.5 weightage
        2. occurrence of entities with the different sentiment - 0.3 weightage
        3. Author - 0.2 weightage
        :param podcast_to_compare: dict containing metadata about podcast 2
        :return: float indicating similarity index
        """
        weights = {'same_sentiment_entity': 0.5, 'different_sentiment_entity': 0.3, 'author': 0.2}

        # Calculate similarity based on entities with the same sentiment
        same_sentiment_entities_similarity = sum(
            1 for entity, sentiment in self.podcast['entities'].items()
            if entity in podcast_to_compare['entities'] and podcast_to_compare['entities'][entity] == sentiment
        ) * weights['same_sentiment_entity']

        # Calculate similarity based on entities with different sentiments
        different_sentiment_entities_similarity = sum(
            1 for entity, sentiment in self.podcast['entities'].items()
            if entity in podcast_to_compare['entities'] and podcast_to_compare['entities'][entity] != sentiment
        ) * weights['different_sentiment_entity']

        # Calculate similarity based on author
        author_similarity = weights['author'] if self.podcast['author'] == podcast_to_compare['author'] else 0

        # Calculate total similarity
        return same_sentiment_entities_similarity + different_sentiment_entities_similarity + author_similarity

    def update_list_of_recommended_podcasts(self, podcast_data: dict, similarity_index: float):
        """
        This function updates the list of top 5 recommended podcasts based on the similarity percentage.
        :param podcast_data: Dictionary containing podcast data
        :param similarity_index: Similarity index of current podcast with the main podcast
        :return: None
        """
        if len(self.recommended_podcasts) == 0:
            self.recommended_podcasts.append((similarity_index, podcast_data))
        else:
            for index, podcast_info in enumerate(self.recommended_podcasts):
                # The following condition checks whether the similarity index of the current podcast is higher than the
                # similarity index of the podcast in the list. If it is, then the current podcast is inserted into the
                # list of top recommended podcasts at the current location
                if podcast_info[0] < similarity_index:
                    self.recommended_podcasts.insert(index, (similarity_index, podcast_data))
                    break
            # This ensures the length of list of recommended podcast remain same
            self.recommended_podcasts = self.recommended_podcasts[:self.top]

    def make_list_of_recommended_podcasts(self):
        """
        This function prints the title and author information of the top 5 similar podcasts calculated using weighted
        sum.
        :return: None
        """
        for document in self.database_connector.get_multiple_podcasts_from_database():
            if document["title"] != self.podcast["title"]:
                podcast_to_compare = self.database_connector.find_podcast_using_title(document["title"])[0]
                similarity_index = self.calculate_similarity(podcast_to_compare)    # Calculate similarity
                self.update_list_of_recommended_podcasts(podcast_to_compare, similarity_index)


if __name__ == '__main__':
    retrieve_podcasts = RetrievePodcasts("63: Zelph Hung Out On Our Shelf")
    print(retrieve_podcasts.podcast)
    retrieve_podcasts.make_list_of_recommended_podcasts()
    print("Top " + str(retrieve_podcasts.top) + " Podcasts:")
    [print(podcast) for podcast in retrieve_podcasts.recommended_podcasts]
