import attr
from decimal import Decimal 


@attr.s(auto_attribs=True, frozen=True)
class Destination(object):
    place_id: str = attr.ib()
    name: str = attr.ib()
    country: str = attr.ib()
    country_code: str = attr.ib()
    latitude: Decimal = attr.ib(converter=lambda x: Decimal(str(x)))
    longitude: Decimal = attr.ib(converter=lambda x: Decimal(str(x)))

    def asdict(self):
        return attr.asdict(self)
