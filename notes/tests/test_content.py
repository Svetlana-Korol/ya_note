from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestListPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )

    def test_test_notes_list_for_different_users(self):
        notes_in_list_for_diff_users = (
            (self.author, True),
            (self.reader, False),
        )
        for user, note_in_list in notes_in_list_for_diff_users:
            self.client.force_login(user)
            with self.subTest(user=user):
                url = reverse('notes:list')
                response = self.client.get(url)
                object_list = response.context['object_list']
                assert (self.note in object_list) is note_in_list


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Просто текст.',
            slug='slug',
            author=cls.author
        )

    def test_authorized_client_has_form(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
            response = self.client.get(url)
            self.assertIn('form', response.context)
            # Проверим, что объект формы соответствует нужному классу формы.
            self.assertIsInstance(response.context['form'], NoteForm)
