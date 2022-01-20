import attr


@attr.s(auto_attribs=True, frozen=True)
class Place(object):
    place_id: str = attr.ib()
    name: str = attr.ib()
    address: str = attr.ib()
    city: str
    state: str
    country: str
    zip_code: str
    latitude: str
    longitude: str
    # Destination_Id is the place_id of the Destination
    destination_id: str

    def asdict(self):
        return attr.asdict(self)
