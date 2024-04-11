import struct
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from lagrange.pb.service.group import GetInfoRspBody


class Sex(IntEnum):
    notset = 0
    male = 1
    female = 2
    unknown = 255


@dataclass
class UserInfo:
    name: str = ""
    country: str = ""
    region: str = ""
    city: str = ""
    email: str = ""
    school: str = ""
    sex: Sex = None
    age: int = None
    birthday: datetime = None
    registered_on: datetime = None

    @classmethod
    def from_pb(cls, pb: GetInfoRspBody) -> "UserInfo":
        rsp = cls()
        for str_field in pb.fields.str_t:
            if not str_field.value:
                continue
            if str_field.type == 20002:
                rsp.name = str_field.to_str
            elif str_field.type == 20003:
                rsp.country = str_field.to_str
            elif str_field.type == 20004:
                rsp.region = str_field.to_str
            elif str_field.type == 20011:
                rsp.email = str_field.to_str
            elif str_field.type == 20020:
                rsp.city = str_field.to_str
            elif str_field.type == 20021:
                rsp.school = str_field.to_str
            elif str_field.type == 20031:
                if str_field.value == b"\x00\x00\x00\x00":
                    continue
                year, month, day = struct.unpack("!HBB", str_field.value)
                if year == 0:
                    year = 1
                if not (month and day):
                    rsp.birthday = datetime(year, 1, 1)
                else:
                    rsp.birthday = datetime(year, month, day)
            else:
                pass
        for int_field in pb.fields.int_t:
            if int_field.type == 20009:
                rsp.sex = Sex(int_field.value)
            elif int_field.type == 20026:
                rsp.registered_on = datetime.fromtimestamp(int_field.value)
            elif int_field.type == 20037:
                rsp.age = int_field.value
            else:
                pass
        return rsp
