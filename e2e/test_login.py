from selenium.webdriver.common.by import By

from .utils import (
    TEST_URL,
    login_valid_user,
    register_valid_user_and_logout,
    visible,
)

URL = f"{TEST_URL}/login"


class TestLogin:
    def test_navbar_contains_login(self, selenium):
        selenium.get(URL)

        nav = visible(selenium, '#nav a[href="/login"]').text
        assert "Sign in" in nav

    def test_it_displays_login_form(self, selenium):
        selenium.get(URL)

        user_form = visible(selenium, "#user-form")
        inputs = user_form.find_elements(By.TAG_NAME, "input")
        assert len(inputs) == 2
        assert inputs[0].get_attribute("id") == "email"
        assert inputs[0].get_attribute("type") == "email"
        assert inputs[1].get_attribute("id") == "password"
        assert inputs[1].get_attribute("type") == "password"

        button = user_form.find_elements(By.TAG_NAME, "button")[-1]
        assert button.get_attribute("type") == "submit"
        assert "Log in" in button.text

        links = user_form.find_elements(By.CLASS_NAME, "links")
        assert links[0].tag_name == "a"
        assert "Register" in links[0].text
        assert links[1].tag_name == "a"
        assert "Forgot password?" in links[1].text
        assert links[2].tag_name == "a"
        assert "Didn't received instructions?" in links[2].text

    def test_user_can_log_in(self, selenium):
        user = register_valid_user_and_logout(selenium)

        login_valid_user(selenium, user)

        menu = visible(selenium, 'summary[aria-label="Account menu"]')
        assert user["username"] in menu.text
        for path in ["/", "/progress", "/workouts/add", "/users", "/profile"]:
            assert visible(selenium, f'.r-primary-nav a[href="{path}"]')
        assert not selenium.find_elements(
            By.CSS_SELECTOR, '#nav a[href="/login"]'
        )
