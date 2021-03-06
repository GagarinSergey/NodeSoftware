# -*- coding: utf-8 -*-
#
# This module (which must have the name queryfunc.py) is responsible
# for converting incoming queries to a database query understood by
# this particular node's database schema.
# 

# library imports 

import sys
from django.db.models import Q
from django.conf import settings
from vamdctap.sqlparse import where2q

import dictionaries
from models import *

import logging
log = logging.getLogger('vamdc.node.queryfu')

def setupResults(sql):
    """
    This function is always called by the software.
    """
    # log the incoming query
    log.debug('sql input: %s'%sql)

    # convert the incoming sql to a correct django query syntax object 
    # based on the RESTRICTABLES dictionary in dictionaries.py
    # (where2q is a helper function to do this for us).
    q = where2q(sql.where, dictionaries.RESTRICTABLES)
    try: 
        q = eval(q) # test queryset syntax validity
    except: 
        return {}

    #react_ds = RxnData.objects.filter(pk__in=(2,4,3862,3863,7975,7976))
    react_ds = RxnData.objects.filter(q)

    # count the number of matches, make a simple trunkation if there are
    # too many (record the coverage in the returned header)
    nreacts=react_ds.count()
    log.debug('number of reaction data: %s'%nreacts)

    sources = Source.objects.filter(pk__in=set(react_ds.values_list('ref_id', flat=True))) 
    nsources = sources.count()

    reacts = Reaction.objects.filter(pk__in=set(react_ds.values_list('reaction_id', flat=True)))
    species = Species.objects.filter(pk__in=reacts.values_list('species'))
    atoms = species.filter(type=1)
    molecules = species.filter(type=2)
    particles = species.filter(type=3)

    for rea in react_ds:
        rea.Reactants = rea.reaction.reactants.all()
        rea.Products = rea.reaction.products.all()

    log.debug('done setting up the QuerySets')
    # Create the header with some useful info. The key names here are
    # standardized and shouldn't be changed.
    headerinfo={\
            'COUNT-ATOMS':atoms.count(),
            'COUNT-MOLECULES':molecules.count(),
            'COUNT-COLLISIONS':nreacts,
            }

    # Return the data. The keynames are standardized. 
    return {\
            'CollTrans':react_ds,
            'Atoms':atoms,
            'Molecules':molecules,
            #'Particles':particles,
            'Sources':sources,
            'HeaderInfo':headerinfo,
            #'Methods':methods
            #'Functions':functions
           }
