class TaskBatch:
    def __init__(self, name, load, region):
        self.name = name
        self.load = load
        self.region = region

    def __repr__(self) -> str:
        return f"{self.name:<14} load: {self.load:<6} region: {self.region:<15}"

    def reduce_load(self, load):
        # this should not go beneath 0
        self.load -= load
        assert self.load >= 0
