import os
import random
import re
import string
from email import policy
from email.parser import Parser

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.util import parse_url

TEST_APP_URL = os.getenv("TEST_APP_URL")
TEST_CLIENT_URL = os.getenv("TEST_CLIENT_URL")
E2E_ARGS = os.getenv("E2E_ARGS")
TEST_URL = TEST_CLIENT_URL if E2E_ARGS == "client" else TEST_APP_URL
EMAIL_URL = os.getenv("EMAIL_URL", "smtp://none:none@0.0.0.0:1025")
parsed_email_url = parse_url(EMAIL_URL)
EMAIL_API_URL = f"http://{parsed_email_url.host}:8025"


def random_string(length=8):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def visible(selenium, selector):
    return WebDriverWait(selenium, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
    )


def logout(selenium):
    visible(selenium, 'summary[aria-label="Account menu"]').click()
    WebDriverWait(selenium, 10).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                '//div[contains(@class, "r-account-options")]/button'
                '[normalize-space()="Logout"]',
            )
        )
    ).click()
    visible(selenium, "#modal .confirm").click()
    visible(selenium, '#nav a[href="/login"]')


def register(selenium, user):
    selenium.get(f"{TEST_URL}/register")
    user_form = visible(selenium, "#user-form")
    username = user_form.find_element(By.ID, "username")
    username.send_keys(user.get("username"))
    email = user_form.find_element(By.ID, "email")
    email.send_keys(user.get("email"))
    password = user_form.find_element(By.ID, "password")
    password.send_keys(user.get("password"))
    accepted_policy = user_form.find_element(By.ID, "accepted_policy")
    accepted_policy.click()
    submit_button = user_form.find_elements(By.TAG_NAME, "button")[-1]
    submit_button.click()


def login(selenium, user):
    selenium.get(f"{TEST_URL}/login")
    user_form = visible(selenium, "#user-form")
    email = user_form.find_element(By.ID, "email")
    email.send_keys(user.get("email"))
    password = user_form.find_element(By.ID, "password")
    password.send_keys(user.get("password"))
    submit_button = user_form.find_elements(By.TAG_NAME, "button")[-1]
    submit_button.click()


def register_valid_user(selenium):
    user_name = random_string()
    user = {
        "username": user_name,
        "email": f"{user_name}@example.com",
        "password": "p@ssw0rd",
    }
    register(selenium, user)
    WebDriverWait(selenium, 60).until(EC.url_changes(f"{TEST_URL}/register"))
    confirm_account(selenium, user)
    return user


def register_valid_user_and_logout(selenium):
    user = register_valid_user(selenium)
    logout(selenium)
    return user


def confirm_account(selenium, user):
    def confirmation_link(_):
        response = requests.get(
            f"{EMAIL_API_URL}/api/v2/search",
            params={"kind": "to", "query": user["email"]},
            timeout=10,
        )
        response.raise_for_status()
        for item in response.json()["items"]:
            message = Parser(policy=policy.default).parsestr(
                item["Raw"]["Data"]
            )
            body = message.get_body(preferencelist=("plain",))
            match = re.search(
                r"Verify your email: (https?://\S+)", body.get_content()
            )
            if match:
                return match.group(1).replace("http://0.0.0.0:5000", TEST_URL)
        return False

    link = WebDriverWait(selenium, 60).until(confirmation_link)
    selenium.get(link)
    visible(selenium, 'summary[aria-label="Account menu"]')


def login_valid_user(selenium, user):
    login(selenium, user)
    visible(selenium, 'summary[aria-label="Account menu"]')
    return user
