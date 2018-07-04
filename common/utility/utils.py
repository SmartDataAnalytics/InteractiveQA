from __future__ import division
from __future__ import print_function
import os
import logging.config
import json
import urllib, urllib2
import config
from multiprocessing.dummy import Pool as ThreadPool
import random, string
from cacheDict import CacheDict


class Struct(object): pass


class Utils:
    cache_path = './caches'
    triple2nl_cache = {}

    @staticmethod
    def set_cache_path(path):
        Utils.cache_path = path
        Utils.triple2nl_cache = CacheDict(os.path.join(Utils.cache_path, 'triple2nl.cache'))

    @staticmethod
    def triple2nl(uri1, uri2, uri3):
        cache_id = uri1 + uri2 + uri3
        if cache_id not in Utils.triple2nl_cache:
            done = False
            try:
                data = {'val1': uri1.encode("ascii", "ignore"),
                        'val2': uri2.encode("ascii", "ignore"),
                        'val3': uri3.encode("ascii", "ignore")}
                result = Utils.call_web_api(
                    config.config['semweb2nl']['endpoint'] + 'triple2nl?',
                    raw_input=data,
                    use_json=False, use_url_encode=True, parse_response_json=False)
                if result is not None:
                    Utils.triple2nl_cache[cache_id] = result
                    done = True
            except:
                pass

            def __extract_label(uri):
                if '/' in uri:
                    return uri[uri.rindex('/') + 1:]
                return uri
            if not done:
                Utils.triple2nl_cache[cache_id] = __extract_label(uri1) + '->' + __extract_label(
                    uri2) + '->' + __extract_label(uri3)
        return Utils.triple2nl_cache[cache_id]

    @staticmethod
    def rand_id(N=10):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

    @staticmethod
    def run_in_parallel(args, *fns):
        pool = ThreadPool(4)
        p_args = [(args, fns[i]) for i in range(len(fns))]
        outputs = pool.map(lambda x: x[1](*x[0]), p_args)
        return outputs

    @staticmethod
    def makedirs(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
        return None

    @staticmethod
    def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
        path = default_path
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)

    @staticmethod
    def call_web_api(endpoint, raw_input=None, use_json=True, use_url_encode=False, parse_response_json=True):
        proxy_handler = urllib2.ProxyHandler({})
        if 'sda-srv' in endpoint or '127.0.0.1' in endpoint:
            opener = urllib2.build_opener(proxy_handler)
        else:
            opener = urllib2.build_opener()
        req = urllib2.Request(endpoint)
        if use_json:
            input = json.dumps(raw_input)
            req.add_header('Content-Type', 'application/json')
        elif use_url_encode:
            input = urllib.urlencode(raw_input)
        else:
            input = raw_input
        try:
            response = opener.open(req, data=input, timeout=config.config["general"]["http"]["timeout"])
            response = response.read()
            if parse_response_json:
                return json.loads(response)
            else:
                return response
        except Exception as expt:
            # print(expt)
            return None

    @staticmethod
    def find_mentions(text, uris):
        output = []
        for uri in uris:
            s, e, dist = Utils.__substring_with_min_levenshtein_distance(str(uri), text)
            if dist <= 5:
                output.append({"uri": uri, "start": s, "end": e})
        return output

    @staticmethod
    def __fuzzy_substring(needle, haystack):
        """Calculates the fuzzy match of needle in haystack,
        using a modified version of the Levenshtein distance
        algorithm.
        The function is modified from the levenshtein function
        in the bktree module by Adam Hupp"""
        m, n = len(needle), len(haystack)

        # base cases
        if m == 1:
            # return not needle in haystack
            row = [len(haystack)] * len(haystack)
            row[haystack.find(needle)] = 0
            return row
        if not n:
            return m

        row1 = [0] * (n + 1)
        for i in range(0, m):
            row2 = [i + 1]
            for j in range(0, n):
                cost = (needle[i] != haystack[j])

                row2.append(min(row1[j + 1] + 1,  # deletion
                                row2[j] + 1,  # insertion
                                row1[j] + cost)  # substitution
                            )
            row1 = row2
        return row1

    @staticmethod
    def __min_farest(values):
        return -min((x, -i) for i, x in enumerate(values))[1]

    @staticmethod
    def __min_nearest(values):
        return min(enumerate(values), key=lambda p: p[1])[0]

    @staticmethod
    def __levenshtein(s1, s2):
        if len(s1) < len(s2):
            return Utils.__levenshtein(s2, s1)

        # len(s1) >= len(s2)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[
                                 j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + 1  # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def __substring_with_min_levenshtein_distance(n, h):
        n = n.lower().replace("_", " ")
        h = h.lower()
        row = Utils.__fuzzy_substring(n, h)
        end = min(Utils.__min_farest(row), len(h) - 1)
        row_rev = Utils.__fuzzy_substring(n[::-1], h[::-1])
        start = max(0, len(h) - Utils.__min_nearest(row_rev) - 1)

        strip = [" ", "?", ".", ",", "'"]
        # stretch the token to be whole word[s]
        while h[start] not in strip and start >= 0:
            start -= 1

        while h[end - 1] not in strip and end < (len(h) - 1):
            end += 1

        # remove invalid chars in head or tail
        for i in range(start, end):
            if h[start] in strip:
                start += 1
            else:
                break

        for i in range(end, start, -1):
            if h[end - 1] in strip:
                end -= 1
            else:
                break

        return start, end, row[end]
