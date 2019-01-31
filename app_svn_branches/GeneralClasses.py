'''
Created on 15 Nov 2018

@author: rudnikp

    1. general item and ItemColl class
    2. general mapping class
    2. commodity class

'''
import re

# ===============================================================================
# general item and ItemColl class
# ===============================================================================
''' 
@info provides a iterable collection class that can be used with arbitrary data class

@usage:

first you define you own data class inheriting from gencls.Item 

import General.GeneralClasses as gencls
class CommodityPrice(gencls.Item):
    def __init__(self,contract_type=None,vol=None,price=None):
        self.loc_dt = None
        self.utc_dt = None
        self.contract_type = contract_type
        self.values = dict()  # "price" : 15.0, "high" : 18.9

then build your collection:

    CommodityPrices = gencls.ItemColl(sheetName)
    for i in range(10) 
        CommodityPrice = CommodityPrice()
        CommodityPrice.loc_dt = loc_dt
        CommodityPrice.values["vol"] = 1.0
        CommodityPrice.values["price"] = 3.55
        CommodityPrices.add(CommodityPrice)        

then you can iterate it in this way (there is an automated str representation)  

    for CommodityPrice in CommodityPrices:
        print (CommodityPrice)

you can retrieve items in the collection by id, name
you can also use regular expressions to search the collection by name and desc





'''


class Item(object):
    """
        @info:
        derived items
            import General.GeneralClasses as gc
            class ConfigItem(gc.Item):

                def __init__(self, product_UID, origin_loc_UID, destination_loc_UID, active):
                    super(ConfigItem, self).__init__()
                    self.product_UID = product_UID
                    self.origin_loc_UID = origin_loc_UID
                    self.destination_loc_UID = destination_loc_UID
                    self.active = active

    """

    def __init__(self, uid=None, name=None, desc=None, info=None):
        self.uid = uid
        self.name = name
        self.desc = desc
        self.info = info
        self.flag = 0

    # representations
    def __repr__(self):
        s = u""
        for x in dir(self):
            if not x.startswith("__"):
                v = getattr(self, x)
                if len(s) > 0:
                    s += ", "
                s = s + "{k}={v}".format(k=x, v=str(v))
        return "{c}, {v}".format(c=self.__class__, v=s)

    def __str__(self):
        return self.__repr__()


class ItemColl(object):
    """
        @info: general collection class

        allows:
        for CommodityPrice in CommodityPrices:
            print (CommodityPrice)
   """

    def __init__(self, name=None):
        self.name = name
        self._idx = 0
        self.coll = list()

    def add(self, item):
        if isinstance(item, Item):
            self.coll.append(item)
        else:
            raise ValueError("Trying to add wrong class that is not a descendend of Item!")

    def append(self, item):
        self.add(item)

    def get(self, uid=None, name=None):
        ret = None
        for item in self.coll:
            if (uid is not None and item.uid == uid) or (name is not None and item.name == name):
                ret = item
                break
        return ret

    def getItems(self, flag=None, regex_expr_name=None, regex_expr_desc=None, uids=None):
        ret = ItemColl()
        if flag is not None:
            for item in self.coll:
                if item.flag == flag:
                    ret.add(item)
        if regex_expr_name is not None:
            for item in self.coll:
                result = re.search(regex_expr_name, self.desc, re.IGNORECASE)
                if result != None:
                    ret.add(item)
        if regex_expr_desc is not None:
            for item in self.coll:
                result = re.search(regex_expr_desc, self.desc, re.IGNORECASE)
                if result != None:
                    ret.add(item)
        if uids is not None and isinstance(uids, list):
            if self.uid in uids:
                ret.add(item)
        return ret

    def __len__(self):
        return len(self.coll)

    def __contains__(self, item):
        return item in self.coll

        # iterator

    def __iter__(self):
        self._idx = 0
        return self

    def __getitem__(self, key):
        return self.coll[key]

    def __next__(self):
        self._idx += 1
        try:
            return self.coll[self._idx - 1]
        except IndexError:
            self._idx = 0
            raise StopIteration  # Done iterating.

    next = __next__  # python2.x compatibility.

    def sort(self, key=None, reverse=False):
        """
            usage example:
                review_item_list.sort(key = lambda x: x.creation_dt, reverse=False )
        """
        self.coll.sort(key=key, reverse=reverse)

    # ===============================================================================


# general mapping class
# ===============================================================================
class XUnit(object):
    def __init__(self, code, name, info=None):
        self.code = code
        self.name = name
        self.info = info


class XMapping(object):
    def __init__(self, code, name, mapped_code, mapped_name, info=None, mapped_info=None):
        self.unit = XUnit(code, name, info)
        self.mapped_unit = XUnit(mapped_code, mapped_name, mapped_info)


class XMappingColl(object):
    def __init__(self):
        self.coll = list()

    def add(self, xmapping):
        self.coll.append(xmapping)

    def get(self, code=None, name=None, mapped_code=None, mapped_name=None):
        ret = None
        for item in self.coll:
            if code is not None:
                if item.unit.code == code:
                    ret = item
                    break
            if name is not None:
                if item.unit.name == name:
                    ret = item
                    break
            if mapped_code is not None:
                if item.mapped_unit.code == mapped_code:
                    ret = item
                    break
            if mapped_name is not None:
                if item.mapped_unit.name == mapped_name:
                    ret = item
                    break
        return ret

    def __len__(self):
        return len(self.coll)

