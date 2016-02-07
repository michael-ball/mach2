class BaseModel():

    def as_dict(self):
        this_dict = {}

        for k in self.__dict__.keys():
            if k != "_db":
                this_dict[k] = getattr(self, k)

        return this_dict
