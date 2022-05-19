#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/comm/sector_mapping.py
#
#  This maps organisatie type from teamleader to a sector for ldap
#  Used in CompanyService

from enum import Enum


class Sector(str, Enum):
    cultuur = 'Cultuur'
    landelijke_private_omroep = 'Landelijke Private Omroep'
    publieke_omroep = 'Publieke Omroep'
    regionale_omroep = 'Regionale Omroep'
    overheid = 'Overheid'


class SectorMapping:
    @staticmethod
    def lookup_sector(type_organisatie):
        sectormap = {
            "ALG - advocatenbureau": None,
            "ALG - kathedrale kerkfabriek": None,
            "ALG - kerkfabriek": None,
            "ALG - sectororganisatie": Sector.cultuur,
            "CUL - archief": Sector.cultuur,
            "CUL - erfgoedbibliotheek": Sector.cultuur,
            "CUL - erfgoedcel": Sector.cultuur,
            "CUL - kunstenorganisatie": Sector.cultuur,
            "CUL - museum (erkend)": Sector.cultuur,
            "CUL - museum (niet-erkend)": None,
            "CUL - openbare bibliotheek": Sector.cultuur,
            "LEV - dienstenbedrijf": None,
            "LEV - digitaliseringsbedrijf": None,
            "LEV - fotograaf": None,
            "LEV - technologiebedrijf": None,
            "MED - landelijke private omroep": Sector.landelijke_private_omroep,
            "MED - mediabedrijf": None,
            "MED - publieke omroep": Sector.publieke_omroep,
            "MED - regionale omroep": Sector.regionale_omroep,
            "OND - deeltijds kunstonderwijs": None,
            "OND - educatieve organisatie": None,
            "OND - educatieve uitgeverij": None,
            "OND - hoger onderwijs": None,
            "OND - leerplichtonderwijs": None,
            "OND - onderwijskoepel": None,
            "OND - vakbond": None,
            "OND - vakvereniging onderwijs": None,
            "OND - volwassenenonderwijs": None,
            "OVH - adviescommissie": Sector.overheid,
            "OVH - commissie Vlaams Parlement": Sector.overheid,
            "OVH - kabinet": Sector.overheid,
            "OVH - overheidsdienst": Sector.overheid
        }

        if type_organisatie is None:
            return None

        return sectormap[type_organisatie]
