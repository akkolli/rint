from selenium.webdriver.common.by import By

from .utils import register_valid_user, visible


class TestProfile:
    def test_it_displays_user_profile(self, selenium):
        user = register_valid_user(selenium)

        visible(selenium, '.r-primary-nav a[href="/profile"]').click()
        header = visible(selenium, ".r-profile-hero")
        assert user["username"] in header.text
        stats = header.find_elements(By.CLASS_NAME, "user-stat")
        assert len(stats) == 3
        for stat, label in zip(
            stats, ["workouts", "following", "followers"], strict=True
        ):
            assert stat.find_element(By.CLASS_NAME, "stat-number").text == "0"
            assert (
                stat.find_element(By.CLASS_NAME, "stat-label").text.lower()
                == label
            )

        visible(
            selenium, f'.athlete-actions a[href="/users/{user["username"]}"]'
        ).click()
        visible(selenium, "#user-infos .profile-about summary").click()
        user_infos = visible(selenium, "#user-infos .profile-about dl")
        assert "Registration date" in user_infos.text
        assert "First name" not in user_infos.text
        assert "Last name" not in user_infos.text
        assert "Birth date" not in user_infos.text
        assert "Location" not in user_infos.text
        assert "Bio" not in user_infos.text
