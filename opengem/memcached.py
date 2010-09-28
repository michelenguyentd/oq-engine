#!/usr/bin/env python
# encoding: utf-8
"""
A simple memcached reader.

"""

import json

import shapes


class Reader(object):
    """Read objects from memcached and translate them into
    our object model.
    
    """
    
    def __init__(self, client):
        self.client = client
    
    def _check_key_in_cache(self, key):
        """Raise an error if the given key is not in memcached."""
        
        if not self.client.get(key):
            raise ValueError("There's no value for key %s!" % key)
        
    def as_curve(self, key):
        """Read serialized versions of hazard curves
        and produce shapes.FastCurve objects.
        
        TODO (ac): How should we handle other metadata?
        """
        
        decoded_model = self._get_and_decode(key)
        
        curves = []
        
        for raw_curves in decoded_model["hcRepList"]:
            for curve in raw_curves["probExList"]:
                curves.append(shapes.FastCurve(
                        zip(raw_curves["gmLevels"], curve)))
        
        return curves
    
    def _get_and_decode(self, key):
        """Get the value from cache and return the decoded object."""
        
        self._check_key_in_cache(key)
        return json.JSONDecoder().decode(self.client.get(key))
    
    def for_shaml(self, key):
        """Read serialized versions of hazard curves
        and produce a dictionary as expected by the shaml writer.
        
        TODO (ac): What about make this generated by an improved
        version of the Curve object?
        """
        
        decoded_model = self._get_and_decode(key)
        
        curves = {}
        
        for set_counter, raw_curves in enumerate(decoded_model["hcRepList"]):
            
            for curve_counter, curve in enumerate(raw_curves["probExList"]):
                data = {}
                
                data["IDmodel"] = "FIXED" # fixed, not yet implemented
                data["vs30"] = 0.0 # fixed, not yet implemented
                data["timeSpanDuration"] = raw_curves["timeSpan"]
                data["IMT"] = raw_curves["intensityMeasureType"]
                data["Values"] = curve
                data["IML"] = raw_curves["gmLevels"]
                data["maxProb"] = curve[-1]
                data["minProb"] = curve[0]
                data["endBranchLabel"] = \
                        decoded_model["endBranchLabels"][set_counter]
                
                lon = raw_curves["gridNode"][curve_counter]["location"]["lon"]
                lat = raw_curves["gridNode"][curve_counter]["location"]["lat"]
                
                curves[shapes.Site(lon, lat)] = data

        return curves
