"""  Module for working with epg.dat file """

import struct
from xml.dom.minidom import parse, Node

from app.eparser.ecommons import BouquetService, BqServiceType


class EPG:

    @staticmethod
    def get_epg_refs(path):
        """ The read algorithm was taken from the eEPGCache::load() function from this source:
            https://github.com/OpenPLi/enigma2/blob/44d9b92f5260c7de1b3b3a1b9a9cbe0f70ca4bf0/lib/dvb/epgcache.cpp#L1300
        """
        refs = []

        with open(path, mode="rb") as f:
            crc = struct.unpack("<I", f.read(4))[0]
            if crc != int(0x98765432):
                raise ValueError("Epg file has incorrect byte order!")

            header = f.read(13).decode()
            if header != "ENIGMA_EPG_V7":
                raise ValueError("Unsupported format of epd.dat file!")

            channels_count = struct.unpack("<I", f.read(4))[0]

            for i in range(channels_count):
                sid, nid, tsid, events_size = struct.unpack("<IIII", f.read(16))
                service_id = "{:X}:{:X}:{:X}".format(sid, tsid, nid)

                for j in range(events_size):
                    _type, _len = struct.unpack("<BB", f.read(2))
                    f.read(10)
                    n_crc = (_len - 10) // 4
                    if n_crc > 0:
                        [f.read(4) for n in range(n_crc)]

                refs.append(service_id)

        return refs


class ChannelsParser:

    @staticmethod
    def get_refs_from_xml(path):
        services = []
        dom = parse(path)

        description = "".join(n.data + "\n" for n in dom.childNodes if n.nodeType == Node.COMMENT_NODE)
        services.append(BouquetService(name=description, type=BqServiceType.MARKER, data=None, num=-1))

        for elem in dom.getElementsByTagName("channels"):
            c_count = 0
            comment_count = 0
            current_data = ""

            if elem.hasChildNodes():
                for n in elem.childNodes:
                    if n.nodeType == Node.COMMENT_NODE:
                        c_count += 1
                        comment_count += 1
                        txt = n.data.strip()
                        if comment_count:
                            services.append(BouquetService(name=txt, type=BqServiceType.MARKER, data=None, num=c_count))
                            comment_count -= 1
                        else:
                            services.append(BouquetService(name=txt,
                                                           type=BqServiceType.DEFAULT,
                                                           data="{}:{}:{}:{}".format(*current_data.split(":")[3:7]),
                                                           num=c_count))
                    if n.hasChildNodes():
                        for s_node in n.childNodes:
                            if s_node.nodeType == Node.TEXT_NODE:
                                comment_count -= 1
                                current_data = s_node.data
        return services


if __name__ == "__main__":
    pass
