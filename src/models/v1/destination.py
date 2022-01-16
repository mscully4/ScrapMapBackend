import attr


@attr.s(auto_attribs=True, frozen=True)
class Destination(object):
    place_id: str = attr.ib()
    name: str = attr.ib()
    country: str = attr.ib()
    country_code: str = attr.ib()
    latitude: float = attr.ib()
    longitude: float = attr.ib()

    def asdict(self):
        return attr.asdict(self)
