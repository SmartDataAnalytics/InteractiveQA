class Oracle:
    def __init__(self):
        pass

    def validate_query(self, qapair, query):
        return qapair.sparql == query

    def answer(self, qapair, io):
        if io.value == 'boolean':
            return "ask " in qapair.sparql.query.lower()
        if io.value == 'count':
            return "count(" in qapair.sparql.query.lower()
        if io.value == 'list':
            return not ("ask " in qapair.sparql.query.lower() or "count(" in qapair.sparql.query.lower())
        io_uri = io.value.uris[0].uri
        if io.type == 'linked':
            return len([uri.uri for uri in qapair.sparql.uris if uri.uri == io_uri]) > 0
        elif io.type == 'type':
            return len([uri for uri in qapair.sparql.uris if uri.is_entity() and io_uri in uri.types]) > 0
        else:
            return False