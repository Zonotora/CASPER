class RequestBatch:
    def __init__(self, name, load, region):
        self.name = name
        self.load = load
        self.region = region

    def __repr__(self) -> str:
        return f"RequestBatch({self.region}, load={self.load})"
