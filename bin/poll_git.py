#!/usr/bin/env python

"""
poll_git.py

Description:

Print a JSON dictionary by polling github for the repositories containing
a given keyword, ordered by the number of forks (descending).


Design Considerations:

This script is run without user authentication. Because of GitHub restrictions,
this may cause a temporary lockout if run too many times within an hour.
"""

import argparse
import json
import sys

import requests


# =========================================================================== #
#                                  GLOBALS                                    #
# =========================================================================== #
BASE_URL = 'https://api.github.com/search/repositories'
QUALIFIERS = '?q=%s&sort=forks&order=desc&per_page=%d&page=%d'

DATA_KEYS = {'id',
             'name',
             'description',
             'language',
             'created_at',
             'html_url',
             'watchers_count',
             'forks_count',
             'owner'}

OWNER_KEYS = {'login', 'id', 'url'}


# =========================================================================== #
#                                  FUNCTIONS                                  #
# =========================================================================== #
def _retrieve_data(keyw, limit, page=1):
    """
    poll_git._retrieve_data

    Recursive function to retrieve all the repositories returned from git
    containing the supplied keyword.

    Git paginates the return values instead of supplying the entire list.
    Initially this call will retrieve page 1 and then recursively call itself
    incrementing the page number until an error code is returned.

    args:
        keyw - (string) Keyword used as a qualifier for the request
        page - (int) Page number of the current request

    Returns:
        Dictionary containing the repository information for the page number
        supplied.

    Design Considerations:
        To maximize efficiency, the 'per_page' qualifier should be set to the
        maximum that GIT allows (currently 100)
    """
    #  Max results per page is 100
    per_page = limit if limit < 100 else 100
    url = BASE_URL + QUALIFIERS % (keyw, per_page, page)

    req = requests.get(url)
    r_json = req.json()

    if limit > 100:
        r_json['items'].extend(_retrieve_data(keyw, limit - 100, page + 1).
                               get('items', []))

    return r_json


def _filter_dict(src_dict, key_set):
    """
    poll_git.filter_dict

    Utility method to remove all keys from a dict except those in the key set

    args:
        src_dict - (dictionary) Dictionary being filtered
        key_set - (set) Set of keys to keep
    """
    for k in set(src_dict.keys()) - key_set:
        src_dict.pop(k)


# =========================================================================== #
#                                   MAIN                                      #
# =========================================================================== #
def main():
    """
    The main function

    Print a JSON dictionary by polling github for the repositories containing
    a given keyword, ordered by the number of forks (descending).

    This main fun
    - parse input args for required input:
      keyword - (str) used to qualify the git GET request
      limit - (int) used to limit the list to the top values specified

    The main function performs the following actions:
    - Issues GET request to GitHub API to return a list of repositories
      that contain the given keyword
    - Determine the number of repositories returned
    - Reduce the list of repositories returned to the top values (number of
        values is determined by the limit arg)
    - Remove extra keys in repositories
    - Print out the dict in valid JSON format

    The dictionary will also contain the keyword searched for, the desired
    number of repositories, the number of repositories returned, and a list
    containing dictionaries of the top repositories containing the following
    fields:
    - id
    - name
    - description
    - language
    - created date
    - html url
    - number of watchers
    - number of forks
    - owner username
    - owner id
    - owner html url


    Design considerations:
    The printed output used the json.dumps function with an indent value of 4
    for readability.

    Usage:
        python ./poll_git.py <KEYWORD> <NUMBER_OF_REPOSITORIES>
    """
    #  parse for provided arguments
    parser = argparse.ArgumentParser()

    #  main is expecting only one arg - that being the test mode flag
    #  test mode flag will be used to optionally commit the db updates
    #  (i.e., if we are in test mode don't commit, do a rollback)
    parser.add_argument('keyword', type=str, help='Keyword')
    parser.add_argument('limit', type=int, help='List limit (1-1000)')
    args = parser.parse_args()

    #  Check to make sure limit it within range
    if args.limit < 1 or args.limit > 1000:
        print 'ERROR: limit [%s] is not in the range 1-1000' % args.limit
        sys.exit(1)

    #  Retrieve all the repositories from GitHub with the keyword, ordered
    #  by descending number of forks
    data = _retrieve_data(args.keyword, args.limit)

    #  pair down repository dict fields
    for item in data['items']:
        _filter_dict(item, DATA_KEYS)
        _filter_dict(item['owner'], OWNER_KEYS)

    #  create final dict
    json_dict = {'keyword': args.keyword,
                 'repository_limit': args.limit,
                 'total_repositories': data['total_count'],
                 'repo_list': data['items']}

    print json.dumps(json_dict, indent=4)


if __name__ == '__main__':
    main()
