class APIBadParameters(Exception):
    code = 400

    def __init__(self, description):
        self.description = description
