from selenium.webdriver.common.by import By

from .utils import logout, register_valid_user, visible


class TestLogout:
    def test_user_can_log_out(self, selenium):
        register_valid_user(selenium)
        logout(selenium)
        assert visible(selenium, '#nav a[href="/register"]')
        assert not selenium.find_elements(By.CSS_SELECTOR, ".r-account-menu")
