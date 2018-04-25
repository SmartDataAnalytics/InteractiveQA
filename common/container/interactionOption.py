from common.utility.uniqueList import UniqueList


class InteractionOption:
    def __init__(self, id, value, query):
        self.id = id
        self.value = value
        if isinstance(query, list):
            self.related_queries = UniqueList(list(query))
        else:
            self.related_queries = UniqueList([query])
        self.__removed = False

    def addQuery(self, query):
        for item in query:
            self.related_queries.addIfNotExists(item)

    def probability(self):
        confidences = [query['complete_confidence'] for query in self.related_queries]
        return sum(confidences) / len(confidences)

    def set_removed(self, val):
        self.__removed = val

    def removed(self):
        return self.__removed

    def __eq__(self, other):
        if isinstance(other, InteractionOption):
            return self.id == other.id and (
                    (isinstance(self.value, dict) and isinstance(other.value, dict) and self.value["uri"] ==
                     other.value["uri"])
                    or self.value == other.value)
        raise NotImplemented

    def __str__(self):
        return str(self.value)
