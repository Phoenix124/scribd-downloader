import requests
import json
from bs4 import BeautifulSoup
from . import const
from . import exceptions
from .internals import REQUEST_TIMEOUT

SCRIBD_LOGIN_URL = "https://www.scribd.com/login"

SCRIBD_LOGIN_HEADERS = {
    "X-Requested-With": "XMLHttpRequest"
}

SCRIBD_LOGIN_DATA = {
    "signup_location": "https://www.scribd.com/"
}


def set_cookies(filepath):
    """
    Reads Scribd premium cookies from the file passed, one
    `name=value` pair per line (e.g. `_scribd_session=...`), as
    copied from a web-browser logged into a premium account.
    """
    with open(filepath, "r") as in_file:
        for line in in_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, sep, value = line.partition("=")
            if not sep:
                raise exceptions.ScribdFetchError("Invalid cookie line, expected name=value: " + line)
            const.premium_cookies[name.strip()] = value.strip()

    if "_scribd_session" not in const.premium_cookies:
        raise exceptions.ScribdFetchError("Cookie file must contain _scribd_session")


def set_credentials(filepath):
    """
    Reads username and password for Scribd premium account
    from the file passed and overrides the default values
    for headers and cookies.
    """
    login_page = requests.get(SCRIBD_LOGIN_URL, timeout=REQUEST_TIMEOUT)
    login_cookies = login_page.cookies

    with open(filepath, "r") as in_file:
        content = in_file.read()
    username, password = content.split()

    SCRIBD_LOGIN_DATA["login_or_email"] = username
    SCRIBD_LOGIN_DATA["login_password"] = password

    # <meta name="csrf-token" content="1k3cOzA9ci6dicSRZce5LjyiH6ird+K/hZ/H7ynnSXiuG/8W1XdozUVSAhUBAIWpIeAlDoTmObzijWW/wDGXUA==" />
    soup = BeautifulSoup(login_page.text, "html.parser")
    csrf = soup.find("meta", dict(name="csrf-token"))
    if csrf:
        SCRIBD_LOGIN_HEADERS["X-CSRF-Token"] = csrf.attrs['content']

    response = requests.post(SCRIBD_LOGIN_URL,
                             headers=SCRIBD_LOGIN_HEADERS,
                             cookies=login_cookies,
                             json=SCRIBD_LOGIN_DATA,
                             timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        raise exceptions.ScribdFetchError("Login failed with status " + str(response.status_code))

    #print(response.text)
    result = json.loads(response.text)
    # {"login":true,"success":true,"user":{"id":514698173}}
    if not result.get("login"):
        # {"form_name":null,"errors":[{"input_name":"login_or_email","msg":"No account found with that email or username. Please try again or sign up."}]}
        errors = result.get("errors")
        if errors:
            raise exceptions.ScribdFetchError("Login error: " + errors[0]["msg"])
        raise exceptions.ScribdFetchError("Login failed: unexpected response from Scribd")

    for cookie in ("_scribd_session", "_scribd_expire"):
        if cookie not in response.cookies:
            raise exceptions.ScribdFetchError("Login failed: missing cookie " + cookie)
        const.premium_cookies[cookie] = response.cookies[cookie]

    return response
