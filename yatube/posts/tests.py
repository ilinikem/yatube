from django.test import TestCase

# Create your tests here.


class TestStringMethods(TestCase):
    def test_length(self):
            self.assertEqual(len('yatube'), 6)

    def test_show_msg(self):
                # действительно ли первый аргумент — True?
            self.assertTrue(False, msg="Важная проверка на истинность")