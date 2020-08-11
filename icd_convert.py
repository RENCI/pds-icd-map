# Convert icd code from 9 or 10 to 11, adapted from Kimberly's code

import sys
import requests
import json
import os
from urllib.parse import quote


base_uri = 'https://id.who.int/icd/'


def _get_autht_headers():
    # get the OAUTH2 token for icd10 access:
    token_endpoint = 'https://icdaccessmanagement.who.int/connect/token'
    scope = 'icdapi_access'
    grant_type = 'client_credentials'
    # set data to post
    client_id = os.environ.get('CLIENT_ID', '')
    client_secret = os.environ.get('CLIENT_SECRET', '')
    if not client_id or not client_secret:
        print("cannot load client id and secret from environment variables")
        return
    payload = {'client_id': client_id,
               'client_secret': client_secret,
               'scope': scope,
               'grant_type': grant_type}
    # make request
    r = requests.post(token_endpoint, data=payload, verify=False).json()
    return {'Authorization': 'Bearer '+r['access_token'],
            'Accept': 'application/json',
            'Accept-Language': 'en',
            'API-Version': 'v2'}


def _get_headers():
    return {'Accept': 'application/json',
            'Accept-Language': 'en'}


def _search_icd_from_9(code):
    newcode = code.replace(".", "")
    uri = "https://clinicaltables.nlm.nih.gov/api/icd9cm_dx/v3/search?terms={}".format(newcode)
    # make request
    headers = {'Accept': 'application/json'}
    r = requests.get(uri, headers=headers, verify=False)
    if r.text == "[0,[],null,[]]":
        sys.stderr.write("WARNING: icd=9,code=" + code + " not found.\n")
        return {"code": code}
    else:
        [tot, no_decimal_codes, _, array] = json.loads(r.text)
        sys.stderr.write(
            "+ tot=" + str(tot) + ",no_dec=" + str(no_decimal_codes[0]) + ",array" + str(array) + "\n")  # xxx
        name = array[0][1].lstrip(" ")
        return {"code": code, "name": name}


def _search_icd_from_10(code):
    uri = base_uri + 'release/10/2016/' + code
    # make request
    r = requests.get(uri, headers=_get_autht_headers(), verify=False)
    if r.text == "Requested resource could not be found":
        # try one more place:
        alt_uri = "http://icd10api.com/?code=" + code + "&desc=long&r=json"
        r = requests.get(alt_uri, headers=_get_headers(), verify=False)
        res = r.text
        parsed_json = json.loads(res)
        if not parsed_json["Response"] or "Description" not in parsed_json:
            return {"code": code}
        else:
            name = parsed_json["Description"]
            return {"code": code, "name": name}
    else:
        res = r.text.replace(":", ": ")
        parsed_json = json.loads(res)
        name = parsed_json["title"]["@value"]
        return {"code": code, "name": name}


def convert_icd_to_11(icd_inputs):
    """
    convert icd code 9 or 10 to 11 chapters
    :param icd_inputs: list of icds in 9 or 10
    :return: converted icd 11 list along with inputs in json format
    """
    icd_jsons = []
    uri_sub_str = "release/11/2019-04/mms/search?includeKeywordResult=false&chapterFilter=01%3B02%3B03%3B04%3B05%3B06%3B07%3B08%3B09%3B10%3B11%3B12%3B13%3B14%3B15%3B16%3B17%3B18%3B19%3B20%3B22%3B23%3B24&useFlexisearch=true&flatResults=false&q="
    icd_10_system_url = 'http://hl7.org/fhir/sid/icd-10-cm'
    icd_9_system_url = 'http://hl7.org/fhir/sid/icd-9-cm'
    for icd_dict in icd_inputs:
        icd_json = {"icd9": {}, "icd10": {}, "icd11": {}}  # if input is icd9, may map to 1 or more icd10, icd11 codes
        if icd_dict['system'] == icd_9_system_url:
            icd_rec = _search_icd_from_9(icd_dict['code'])
            icd = 9
            icd_json['icd9'] = icd_rec
        elif icd_dict['system'] == icd_10_system_url:
            icd_rec = _search_icd_from_10(icd_dict['code'])
            icd = 10
            icd_json['icd10'] = icd_rec
        else:
            icd_res = {}
            icd = ''
        name = icd_rec.get('name', '')
        if not name:
            print("input icd code {} cannot be found".format(icd_dict['code']))
            return
        uri = base_uri + uri_sub_str + quote(str(name))

        r = requests.get(uri, headers=_get_autht_headers(), verify=False)
        if r.text == "Requested resource could not be found":
            print("icd=11, name=[{}] not found".format(name))
            return

        res = r.text.replace(":", ": ")
        parsed_json = json.loads(res)
        if len(parsed_json["destinationEntities"]) == 0:
            print("icd 11 name=[{}] not found, icd={}, code={} not found".format(name, icd, icd_dict['code']))
            return
        # find highest score
        score = -1
        chapter = ""
        # xxx use highest scoring result
        for entity in parsed_json["destinationEntities"]:
            # filter chapter 21, "Symptoms, signs or clinical findings, not elsewhere classified"
            if entity["chapter"] == "21":
                continue
            if entity["score"] > score:
                score = entity["score"]
                icd_json["icd11"] = {"chapter": entity["chapter"],
                                     "code": entity.get("theCode", "null"),
                                     "propertyId": "stemId:" + entity["stemId"],
                                     "label": entity["title"],
                                     "score": entity["score"],
                                     "query": name}
            for PV in entity["matchingPVs"]:
                if PV["score"] > score:
                    score = PV["score"]
                    icd_json["icd11"] = {"chapter": entity["chapter"],
                                         "code": entity.get("theCode", "null"),
                                         "propertyId": PV["propertyId"],
                                         "label": PV["label"],
                                         "score": PV["score"],
                                         "query": name}
        icd_jsons.append(icd_json)

        return icd_jsons
