#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  Utilities for request sessions
#  v1.2.2
# ******************************************


"""
Utilities for request sessions:
    - requests with relative urls on a specified base_url
    - create & keep a login session for a website
    - save/load sessions
    - download files
"""

import os

# Load external general utils - include needed utils after dev
# ----------------------------------------------------
# Get this scripts parent folder path
# - dot .. form would be only relativ to the current working directory
from inspect import currentframe, getframeinfo

C_Path_ThisModule = getframeinfo(currentframe()).filename
C_Path_ParentFolder = os.path.dirname(C_Path_ThisModule)
C_Path_Python_Projects = os.path.dirname(C_Path_ParentFolder)
C_Folder_General_Utils = os.path.join(C_Path_Python_Projects, "utils_general")
C_Path_Module_Logins = os.path.join(C_Path_Python_Projects, "logins")

from utils.module_manager import ModuleManager

ModuleManager = ModuleManager()
utils_general = ModuleManager.import_module(C_Folder_General_Utils, "utils_general")
login_form = ModuleManager.import_module(C_Path_Module_Logins, "login_form")
# ----------------------------------------------------


# dill is an advanced version of pickle
import dill as pickle  # req: https://github.com/uqfoundation/dill
import requests  # req: https://github.com/kennethreitz/requests
import datetime
import time
import logging
import json

C_UserAgent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0")

#C_LoginForm_Selector = '//form[@action="login_url"]'


class xSession(requests.Session):
    """
    Advanced requests session that allows setting a base url (like for an API) and doing following requests with relative urls
    """
    def __init__(self, base_url, api_auth=None, auth_method='param', user_agent="Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.trust_env = False
        self.headers.update({"user-agent": user_agent})
        if api_auth and auth_method == 'param':
            self.auth = ParamAuth(api_auth)

    # overwrite
    def request(self, method='get', url="", expectCode={'post': requests.codes.created}, debug=False, **kwargs):
        # logging.info("\n" + f"Start API request: {mode}" + "\n")
        results = {'data': None, 'errorCodes': []}
        if (method == 'head'): kwargs.setdefault('allow_redirects', False)
        try:
            if self.base_url and url.startswith('/'): url = self.base_url + url
            # call normal request function
            response = super().request(method=method, url=url, **kwargs)

            # raise exception in case of invalid request
            if (method in expectCode) and (response.status_code != expectCode[method]):
                raise requests.exceptions.RequestException(f"[ExpectCode_Error] response.status_code = {response.status_code}")
            else:
                response.raise_for_status()
                # if everything is good until here, save the response data
                try:
                    results['data'] = response.json()
                except:
                    pass

        except requests.exceptions.HTTPError as err_h:
            results['errorCodes'].append(err_h)
        except requests.exceptions.ConnectionError as err_c:
            results['errorCodes'].append(err_c)
        except requests.exceptions.Timeout as err_t:
            results['errorCodes'].append(err_t)
        except requests.exceptions.RequestException as err:
            results['errorCodes'].append(err)

        if debug:
            logging.info(debug_request(response))
            if results['data']:
                logging.info("request_data:  " + "\n" + utils_general.get_jsonStr(results['data'], indent=2) + "\n")

        return results


class ParamAuth(requests.auth.AuthBase):
    """
    Authenticator that attaches a set of parameters to the requests url string (e.g. an API key)
    """
    def __init__(self, params):
        self.params = params

    def __call__(self, request):
        if self.params:
            request.prepare_url(request.url, self.params)
        return request


# toDo: for session_timeout_minutes new param for hours and days
class RequestsSessionWriter:
    """
    Handles and saves requests sessions. It also keeps track of proxy settings.
    It maintains a cache-file for restoring session data from earlier
    script executions.
    """

    def __init__(
        self,
        path_sessionFolder,
        session_timeout_minutes=0,  # default: never expire
        proxy_urls=None,
        user_agent=C_UserAgent,
        need_login=False,
    ):

        utils_general.ensure_path(path_sessionFolder)
        self.path_session = os.path.join(
            path_sessionFolder, os.path.basename(path_sessionFolder) + ".dat"
        )
        self.timeout_minutes = session_timeout_minutes

        proxies = {}
        if proxy_urls:
            for proxy_url in proxy_urls:
                connectionType = proxy_url.split("://")[0]
                proxies[connectionType] = proxy_url
                # with login: + C_Proxy_User + ':' + C_Proxy_pw + '@' + proxy_address}
        self.proxies = proxies
        self.user_agent = user_agent
        self.need_login = need_login
        self.session = None

    # toDo: versioning of sessions after a new login to be able to revert to a working one in case of a bad new session
    def save_session(self):
        # if os.path.exists(path_source):
        # root, ext = os.path.splitext(self.baseFilename)
        # os.rename(self.path_session, self.path_session)
        with open(self.path_session, "wb") as f:
            pickle.dump(self.session, f)

    # toDo: timeout error in days hours minutes
    def load_session(self):
        is_old_session = False
        if os.path.exists(self.path_session):
            saved_session_delta = (
                datetime.datetime.now() - self.get_date_saved_session()
            )
            days_hours_minutes = utils_general.get_timedelta_d_h_min(saved_session_delta)
            msg = f"Old requests session found:  (Created: {days_hours_minutes} ago)"
            logging.info(msg)
            if (
                utils_general.get_timedelta_min(saved_session_delta) < self.timeout_minutes
            ):  # only re-load session if file is not too old
                with open(self.path_session, "rb") as f:
                    self.session = pickle.load(f)
                if (
                    self.session.proxies == self.proxies
                ):  # old session with other proxies is useless
                    is_old_session = True
                    msg = "Session loaded"
            else:
                msg = (
                    "Session is too old !"
                    + "\n"
                    + f"Timeout is set to:  {self.timeout_minutes}"
                )
        else:
            msg = "No old requests session found !"

        logging.info(msg)

        if not is_old_session:  # create new requests session
            msg = "Creating new requests session !"
            logging.info(msg)
            self.session = requests.Session()
            self.session.trust_env = False
            self.session.proxies = self.proxies
            self.session.headers.update({"user-agent": self.user_agent})
            if not self.need_login:
                self.save_session()

        return is_old_session

    def get_session(self):
        if not self.session:
            self.load_session()
        return self.session

    def get_date_saved_session(self):
        return datetime.datetime.fromtimestamp(os.path.getmtime(self.path_session))


# toDo: when to do a new login - how long is the login cookie valid ?
class RequestsLogin(RequestsSessionWriter):
    """
    Handles and saves requests sessions to disk (see RequestsSessionWriter) and adds
    the functionality to save and load a logged in session for a specific page.
    """

    def __init__(
        self,
        page_name,
        login_url,
        username,
        password,
        path_sessionFolder,
        login_test_string="",
        login_test_url=None,
        session_timeout_minutes=70 * 24 * 60,  # 70 days
        max_login_tries=3,
        login_cooldown_time_ms=50,
        proxy_urls=None,
        user_agent="Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        force_login=False,
    ):
        """
        'login_test_string' is being searched in the responses html to make sure, you've properly been logged in
        'proxies' is of format { 'https' : 'https://user:pass@server:port', 'http' : ...
        'login_data' is sent as post data (dictionary of id : value).
        'session_timeout_minutes' is used to determine when to re-login
        """
        super().__init__(
            path_sessionFolder,
            session_timeout_minutes,
            proxy_urls,
            user_agent,
            need_login=True,
        )
        self.page_name = page_name
        self.login_url = login_url
        self.username = username
        self.password = password
        self.login_test_string = login_test_string
        self.login_test_url = login_test_url or login_url
        self.max_login_tries = max_login_tries
        self.login_cooldown_time_ms = login_cooldown_time_ms

        """
        Try to read last saved session from cache file. If this fails
        do proper login. If the last cache access was too old, also perform a proper login.
        Always updates session cache file.
        """
        is_old_session = False
        is_login = False
        need_newLogin = True
        is_old_session = self.load_session()
        if is_old_session and not force_login:
            # test old logged in session with restricted url
            is_login = self.test_login()
            if is_login:
                logging.info(f"Loaded session is still logged in:  {self.page_name}")
                need_newLogin = False
            else:
                logging.info(f"Loaded session is not logged in:  {self.page_name}")

        if need_newLogin:
            logging.info(f"Performing new login:  {self.page_name}")
            if not self.login():
                # no login could be established, so the session is useless
                self.session = None

    def login(self):
        """
        Create new logged in session
        """

        # toDo: how to load Firefox cookie ??
        # logging.info(requests.utils.dict_from_cookiejar(self.session.cookies))

        # try to login for the set number of times, login_cooldown_time_ms is used between the tries
        for _ in range(self.max_login_tries):
            # analyze login form
            response = self.session.get(self.login_url)
            form_data = login_form.extract_form_data(
                self.login_url, response.text, selector = f'//form[@action="{self.login_url}"]'
            )

            # "fill in" login form virtually
            form_login = login_form.prepare_login(
                form_data, self.username, self.password
            )

            # try login with build form input as payload
            # a real user would have visited the page first and then submit the login form, so set the matching "referer"
            self.session.headers.update({"Referer": self.login_url})
            response = self.session.post(
                form_login["post_url"],
                data=form_login["login_data"],
                proxies=self.proxies,
            )

            # wait for the login process
            utils_general.sleep_ms(100)

            # test login
            is_login = self.test_login()
            if is_login:
                break
            else:
                utils_general.sleep_ms(self.login_cooldown_time_ms)

        if is_login:
            self.save_session()  # save new login to reset session timeout
            logging.info(f"Login successful:  {self.page_name}")
        else:
            # what login data did the server received from us
            msg = json.dumps(
                form_login, ensure_ascii=False, indent=2
            )  # print_request(response.request)
            logging.info(
                f"Error: Login NOT successful:  {self.page_name}"
                + "\n"
                + "Login Data:"
                + "\n"
                + msg
            )

        return is_login

    def test_login(self):
        response = self.session.get(self.login_test_url)
        return self.login_test_string.lower() in response.text.lower()

    # toDo:
    # def update_login_data_tokens(self):
    # token_marker = 'find_token'
    # for key,value in self.login_input.items():  # fastest way, if Key+Value are needed
    # if isinstance(value, str) and value == token_marker:
    # self.login_input[key] = self.session.cookies.get(key, "")    # return empty string if token has another name
    # self.login_input['next'] = '/'
    # old: parsing html for csrf token instead of loading cookie, problem: sometimes it doesn't exist in the source code
    # if isinstance(value, str) and value.startswith(token_marker):
    # value_begin = value.lstrip(token_marker)
    # sourcecode = response.text
    # token = load_value(sourcecode, value_begin)
    # self.login_input[key] = token


def isServerConnection(browser, test_url):
    """Check if the Proxy Server and destination site are working"""
    try:
        response = browser.get(test_url)
        response.raise_for_status()  # for no exception use: response.status_code == requests.codes.ok
        isConnection = True
        # print(response.headers)            # sever infos
        # print(response.request.headers)    # eigene gesendete infos z.B. useragent
    except:
        isConnection = False
    return isConnection



def load_value(text, value_begin):
    """
    Loads the set value following the given property; the first surrounding character has to be submitted like:
      load_value(sourcecode, '"myparam" type="hidden" value="'
    The function looks for the closing character and returns the text between those borders as the value
    Note: For complex analysis better use the lxml library
    """
    index_substring_begin = text.find(value_begin)
    if (index_substring_begin == -1):
        return None
    else:
        char_frame = value_begin[-1]
        index_value_start = index_substring_begin + len(value_begin)
        for i in range(index_value_start, len(text)):
            char = text[i]
            if (char == char_frame):
                index_value_end = i
                break
        return text[index_value_start:index_value_end]


# v1.1
def load_json_object(text, object_begin):
    """
    Loads the related value object following the given property; the first surrounding character has to be submitted like:
      load_json_object(sourcecode, '"myparam" type="hidden" value="'
    The function looks for the final closing character and returns the parsed json object between those borders
    Note: For complex analysis better use the lxml library
    """
    import json

    search_key = object_begin[:-1].strip
    print("json object search_key = '" + search_key + "'")

    index_substring_begin = text.find(search_key)
    if (index_substring_begin == -1):
        return None
    else:
        char_begin = object_begin[-1]
        if char_begin == "{":
            char_end = "}"
        elif char_begin == "[":
            char_end = "]"
        index_object_start = index_substring_begin + len(object_begin) - 1
        count_brackets_open = 1
        # count opening and closing brackets following the first opening bracket to determine the final closing bracket
        for i in range(index_object_start + 1, len(text)):
            char = text[i]
            if char == char_begin:
                count_brackets_open += 1
            elif char == char_end:
                count_brackets_open -= 1
                if count_brackets_open == 0:
                    index_object_end = i + 1
                    break
        try:
            return json.loads(text[index_object_start:index_object_end])
        except:
            return None


def debug_request(response):
    """
    Debug inforamtion about the received response: status_code, server data, own send data e.g. useragent
    """
    response_info = "response.status_code:  " + str(response.status_code) + "\n" + \
                    "response.headers:" + "\n" + get_requestHeaderStr(response.headers, indent=2) + "\n" + \
                    "response.request.headers:" + "\n" + get_requestHeaderStr(response.request.headers, indent=2)
    return response_info


def get_requestHeaderStr(header, indent=None):
    return utils_general.get_jsonStr(dict(header), indent=indent)


# path_folder, file_name separated cause linux files need no extensions: so from paths only you cannot distinguish between files/folders
def download_file(browser, url, path_folder, file_name="", downloadAtOnce_max_MB=50):
    if (not os.path.isdir(path_folder)):
        print("path_folder does not exist: " + path_folder)
        return None
    else:
        head = browser.head(url)
        if (head.status_code != requests.codes.ok):  # for exception use: head.raise_for_status()
            return None  # HTTP Connection Error
        else:
            headers = head.headers
            content_type = headers.get("content-type")
            # check if url is downloadable
            if ("html" in content_type.lower()):
                return None
            else:
                if (
                    not file_name
                ):  # try to get filename from headers or use last part of url
                    content_disp = headers.get("content-disposition")
                    if content_disp:
                        import re

                        file_names = re.findall('filename="?(.+[^"])"?', content_disp)
                        if file_names:
                            file_name = file_names[0]
                        else:
                            file_name = None
                    else:
                        file_name = None
                    if (file_name is None):
                        file_name = url.rsplit("/", 1)[1]

                path_file = os.path.join(os.path.normpath(path_folder), file_name)
                try:
                    content_len = headers.get(
                        "content-length"
                    )  # check the file size and choose best download option
                    if (
                        content_len
                        and int(content_len) >= 1048576 * downloadAtOnce_max_MB
                    ):
                        # large file: download file as stream
                        response = browser.get(url, stream=True, allow_redirects=True)
                        with open(path_file, "wb") as fo:
                            for chunk in response.iter_content(
                                chunk_size=1024 * 64
                            ):  # chunk-size: 64KB
                                fo.write(chunk)
                    else:
                        # small file: downloadfile at once
                        response = browser.get(url, allow_redirects=True)
                        with open(path_file, "wb") as fo:
                            fo.write(response.content)

                    return path_file
                except:
                    print("download_path error")
                    print(content_disp)
                    print(path_file)
                    return None


def print_request(req):
    """
    Pay attention to formatting used in this function:
    The pretty printing may differ from the actual request
    """
    return "{}\n{}\n{}\n\n{}".format(
        "-----------START-----------",
        req.method + " " + req.url,
        "\n".join("{}: {}".format(k, v) for k, v in req.headers.items()),
        req.body
    )


# toDo: save and load only the cookie jar instead of a whole session

# def save_cookies(requests_cookiejar, path_file):
#     with open(path_file + ".pkl", 'wb') as f:
#         pickle.dump(requests_cookiejar, f)


# def load_cookies(path_file):
#     with open(path_file + ".pkl", 'rb') as f:
#         return pickle.load(f)


# def import_requestsCookies_to_selenium(requests_cookiejar, selenium_driver):
#     cookies = [
#         {'name': key, 'value': value} for key, value in requests_cookiejar.items()
#     ]
#     for cookie in cookies:
#         selenium_driver.add_cookie(cookie)

