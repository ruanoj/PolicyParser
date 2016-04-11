__author__ = 'Stavros Konstantaras (stavros@nlnetlabs.nl)'
import logging

import requests

import errors


class Communicator:
    def __init__(self, db_url, source, alternatives):

        def _getAlternatives(alternatives):
            s = ""
            for i in alternatives:
                s += "&source=%s" % i

            return s

        self.db_url = db_url
        self.source = source
        self.other_sources = _getAlternatives(alternatives)
        self.session = requests.session()

    def getPolicyByAutnum(self, autnum):
        db_reply = None
        try:
            db_reply = self._sendDbRequest(self._searchURLbuilder(autnum, None, (), ('r')))
            logging.debug("Policy received for %s" % autnum)
        except errors.RIPEDBError:
            logging.error("Failed to receive policy for %s due to RIPE DB error." % autnum)
            pass
        except errors.SendRequestError as e:
            logging.error('Get policy failed. %s' % e)
            pass
        return db_reply

    def getFilterSet(self, value):
        #
        # Can make requests for as-set, route-set
        #
        db_reply = None
        try:
            db_reply = self._sendDbRequest(self._searchURLbuilder(value, None, (), ('r')))
        except errors.RIPEDBError:
            logging.error('Get Filter failed for %s due to RIPE DB error.' % value)
            pass
        except errors.SendRequestError as e:
            logging.error('Get all routes failed for %s. %s' % (value, e))
            pass
        return db_reply

    def getRoutesByAutnum(self, autnum, ipv6_enabled=False):

        db_reply = None
        if ipv6_enabled:
            url = self._searchURLbuilder(autnum, "origin", ("route", "route6"), ('r'))
        else:
            url = self._searchURLbuilder(autnum, "origin", ("route"), ('r'))

        try:
            db_reply = self._sendDbRequest(url)
        except errors.RIPEDBError:
            logging.error('Get all routes failed for %s due to RIPE DB error' % autnum)
            pass
        except errors.SendRequestError as e:
            logging.error('Get all routes failed for %s. %s' % (autnum, e))
            pass
        return db_reply

    def _searchURLbuilder(self, query_string, inverse_attribute, type_filters, flags):
        """
        Example:
            http://rest.db.ripe.net/search.xml?query-string=as199664&type-filter=route6&inverse-attribute=origin
        """

        new_url = "/search.xml?query-string=%s&source=%s" % (query_string, self.source)
        new_url += self.other_sources

        if inverse_attribute is not None:
            new_url += "&inverse-attribute=%s" % inverse_attribute

        for f in type_filters:
            new_url += "&type-filter=%s" % f

        for f in flags:
            new_url += "&flags=%s" % f

        return self.db_url + new_url

    def _sendDbRequest(self, db_url):

        try:
            # headers = {'Content-Type': 'application/json'}
            headers = {'Accept': 'application/xml'}
            r = self.session.get(db_url, headers=headers)
            if r.status_code == 200:
                # return r.text.encode(encoding='utf-8')
                return r.content
            elif r.status_code == 400:
                logging.warning("RIPE-API: The service is unable to understand and process the request.")
                raise errors.RIPEDBError("RIPE-API_ERROR_400")
            elif r.status_code == 403:
                logging.warning("RIPE-API: Query limit exceeded.")
                raise errors.RIPEDBError("RIPE-API_ERROR_403")
            elif r.status_code == 404:
                logging.warning("RIPE-API: No Objects found")
                raise errors.RIPEDBError("RIPE-API_ERROR_404")
            elif r.status_code == 409:
                logging.warning("RIPE-API: Integrity constraint violated")
                raise errors.RIPEDBError("RIPE-API_ERROR_409")
            elif r.status_code == 500:
                logging.warning("RIPE-API: Internal Server Error")
                raise errors.RIPEDBError("RIPE-API_ERROR_500")
            else:
                logging.warning("Unknown RIPE-API response (%s)" % r.status_code)
                raise errors.RIPEDBError("RIPE-API_ERROR_UNKNOWN")
        except:
            # dunno, we got another type of Error
            raise errors.SendRequestError
