import attr
from decimal import Decimal

@attr.s(auto_attribs=True, frozen=True)
class Place(object):
    place_id: str
    name: str
    address: str
    city: str
    state: str 
    country: str
    zip_code: str
    latitude: Decimal = attr.ib(converter=lambda x: Decimal(str(x)))
    longitude: Decimal = attr.ib(converter=lambda x: Decimal(str(x)))
    # Destination_Id is the place_id of the Destination
    destination_id: str

    def asdict(self):
        return attr.asdict(self)
