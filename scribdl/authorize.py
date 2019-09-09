import requests

from . import const


SCRIBD_LOGIN_URL = "https://www.scribd.com/login"

SCRIBD_LOGIN_HEADERS = {
    "Accept-Encoding": "gzip",
    "X-Requested-With": "XMLHttpRequest"
}

SCRIBD_LOGIN_DATA = {
    "signup_location": "https://www.scribd.com/"
}


def set_credentials(filepath):
    """
    Reads username and password for Scribd premium account
    from the file passed and overrides the default values
    for headers and cookies.
    """
    login_page = requests.get(SCRIBD_LOGIN_URL)
    login_cookies = {"_scribd_session": login_page.cookies["_scribd_session"]}

    with open(filepath, "r") as in_file:
        content = in_file.read()
    username, password = content.split()

    SCRIBD_LOGIN_DATA["login_or_email"] = username
    SCRIBD_LOGIN_DATA["login_password"] = password

    response = requests.post(SCRIBD_LOGIN_URL,
                             headers=SCRIBD_LOGIN_HEADERS,
                             cookies=login_cookies,
                             data=SCRIBD_LOGIN_DATA)

    const.premium_cookies["_scribd_session"] = response.cookies["_scribd_session"]
    const.premium_cookies["_scribd_expire"] = response.cookies["_scribd_expire"]

    return response
