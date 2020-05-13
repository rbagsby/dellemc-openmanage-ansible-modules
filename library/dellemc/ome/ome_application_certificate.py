#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.0.12
# Copyright (C) 2020 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ome_application_certificate
short_description: This module allows to generate a CSR.
version_added: "2.9"
description:
  - This module allows the generation a new certificate signing request (CSR).
options:
  hostname:
    description: Target IP address or hostname.
    type: str
    required: True
  username:
    description: Target username.
    type: str
    required: True
  password:
    description: Target user password.
    type: str
    required: True
  port:
    description: Target HTTPS port.
    type: int
    default: 443
  command:
    description:
      - C(generate_csr) allows the generation of a CSR.
      - The following options are applicable for this command I(distinguished_name),
        I(department_name), I(business_name), I(locality), I(country_state),
        I(country), I(email).
    type: str
    default: generate_csr
    choices: [generate_csr]
  distinguished_name:
    description: Name of the certificate issuer.
    type: str
  department_name:
    description: Name of the department that issued the certificate.
    type: str
  business_name:
    description: Name of the business that issued the certificate.
    type: str
  locality:
    description: Local address of the issuer of the certificate.
    type: str
  country_state:
    description: State in which the issuer resides.
    type: str
  country:
    description: Country in which the issuer resides.
    type: str
  email:
    description: Email associated with the issuer.
    type: str

requirements:
    - "python >= 2.7.5"
author: "Felix Stephen (@felixs88)"
'''

EXAMPLES = r'''
---
- name: Generate a certificate signing request.
  ome_application_certificate:
    hostname: "192.168.0.1"
    username: "username"
    password: "password"
    command: "generate_csr"
    distinguished_name: "hostname.com"
    department_name: "Remote Access Group"
    business_name: "Dell Inc."
    locality: "Round Rock"
    country_state: "Texas"
    country: "US"
    email: "support@dell.com"

'''

RETURN = r'''
---
msg:
  type: str
  description: Overall status of the certificate signing request.
  returned: always
  sample: "Successfully generated certificate signing request."
csr_status:
  type: dict
  description: details of the generated certificate.
  returned: on success
  sample:
    {"CertificateData": "-----BEGIN CERTIFICATE REQUEST-----MIIFFjCCAv4
      CAQAwgZ8xCzAJBgNVBAYTAlVTMQ4wDAYDVQQIDAVUZXhhczETMBEGA1UEBwwKUm91
      bmQgUm9jazESMBAGA1UECgwJRGVsbCBJbmMuMRwwGgYDVQQLDBNSZW1vdGUgQWNjZ
      XNzIEdyb3VwMRwwGgYDVQQDDBNob3N0bmN8Mq6gnvxVmucGbUGmRyrXizGcpTCj5p
      Uv7cALZWqoHblPirAgjmJ8PipTkV93bWr0i34tUJgEb9g/aHOJ6nV4zAyc3zhfqjt
      p4PHAaBqIXPe0tbiqj7WZwE6GPPaW5seRGvzAIPuwn4kod4tXB0DQt4kSIh9TyCSG
      mh5mBAMdOD7Wd0ddXxmeoFJPa/sYQJZarJ/TPr2JAJAAKdxz2XLPokLHmjG02Xje3
      RWQDNm+ngR/UTdXs/51kLrSwlU2LXFaQeBdcrwMdiZCOJPsfl6kf9fxobvqScdRYl
      gjJO7S5UcjJkBkeNURc080N9DCknV4bO1lo9BOA4aEhjo9gFFIUNk8iscMJJqyvHh
      BhzRSWH6fx7u9NGhnlDEOoyJnjceuI7zDS3CT/7pByuCoDc+dK2DezansSJHV4xYC
      eBmO14MpukxfoMxbSXZUdfkQgZZ1LmJGTYH0omGIm0KC+7g2ITZf1FrR8HcjEbKgV
      ZopugdSPXGp4P7eLRA/xIIp3GbrRXbSAumAO5fNefVsIzxZ34fw5O+msj/IH/IAJy
      EP3fq8iflVyV3hQjlUPSq/ZGYy7vPvwZHGhPPDXjvNVgyyD7zKSOkKZIyOL2Xvpom
      1cuJ1veYniuZkVvENkRNxzTmKlzUlYk4326Xauw==-----END CERTIFICATE REQUEST-----"
    }
error_info:
  description: Details of the HTTP error.
  returned: on HTTP error
  type: dict
  sample:
    {
        "error": {
            "code": "Base.1.0.GeneralError",
            "message": "A general error has occurred. See ExtendedInfo for more information.",
            "@Message.ExtendedInfo": [
                {
                    "MessageId": "CSEC9002",
                    "RelatedProperties": [],
                    "Message": "Unable to upload the certificate because the certificate file provided is invalid.",
                    "MessageArgs": [],
                    "Severity": "Critical",
                    "Resolution": "Make sure the CA certificate and private key are correct and retry the operation."
                }
            ]
        }
    }
'''

import json
from ssl import SSLError
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError, SSLValidationError


def get_resource_parameters(module):
    command = module.params["command"]
    csr_uri = "ApplicationService/Actions/ApplicationService.{0}"
    method = "POST"
    if command == "generate_csr":
        uri = csr_uri.format("GenerateCSR")
        payload = {"DistinguishedName": module.params["distinguished_name"],
                   "DepartmentName": module.params["department_name"],
                   "BusinessName": module.params["business_name"],
                   "Locality": module.params["locality"], "State": module.params["country_state"],
                   "Country": module.params["country"], "Email": module.params["email"]}
    return method, uri, payload


def main():
    module = AnsibleModule(
        argument_spec={
            "hostname": {"required": True, "type": "str"},
            "username": {"required": True, "type": "str"},
            "password": {"required": True, "type": "str", "no_log": True},
            "port": {"required": False, "type": "int", "default": 443},
            "command": {"type": "str", "required": False,
                        "choices": ["generate_csr"], "default": "generate_csr"},
            "distinguished_name": {"required": False, "type": "str"},
            "department_name": {"required": False, "type": "str"},
            "business_name": {"required": False, "type": "str"},
            "locality": {"required": False, "type": "str"},
            "country_state": {"required": False, "type": "str"},
            "country": {"required": False, "type": "str"},
            "email": {"required": False, "type": "str"},
        },
        required_if=[["command", "generate_csr", ["distinguished_name", "department_name",
                                                  "business_name", "locality", "country_state",
                                                  "country", "email"]],
                     ],
        supports_check_mode=False
    )
    try:
        with RestOME(module.params, req_session=True) as rest_obj:
            method, uri, payload = get_resource_parameters(module)
            command = module.params.get("command")
            resp = rest_obj.invoke_request(method, uri, data=payload)
            if resp.success:
                if command == "generate_csr":
                    module.exit_json(msg="Successfully generated certificate signing request.",
                                     csr_status=resp.json_data)
    except HTTPError as err:
        module.fail_json(msg=str(err), error_info=json.load(err))
    except URLError as err:
        module.exit_json(msg=str(err), unreachable=True)
    except (IOError, ValueError, SSLError, TypeError, ConnectionError, SSLValidationError) as err:
        module.fail_json(msg=str(err))
    except Exception as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()
