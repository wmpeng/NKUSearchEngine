from unittest import TestCase
import mytool


class TestMyUtil(TestCase):
    def test_diff_ratio(self):
        print(mytool.MyUtil.same_ratio("a", "b"))
