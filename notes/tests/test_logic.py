from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify
from pytest_django.asserts import assertRedirects, assertFormError

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')

    def test_user_can_create_note(self):
        notes_in_db_before_add = Note.objects.count()
        response = self.author_client.post(self.add_url, data=self.form_data)
        assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, notes_in_db_before_add+1)
        new_note = Note.objects.get(id=self.note.id+1)
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        response = self.client.post(self.add_url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.add_url}'
        assertRedirects(response, expected_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(self.add_url, data=self.form_data)
        assertFormError(response, 'form', 'slug', errors=(
            self.note.slug + WARNING)
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        notes_in_db_before_add = Note.objects.count()
        self.form_data.pop('slug')
        response = self.author_client.post(self.add_url, data=self.form_data)
        assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, notes_in_db_before_add+1)
        new_note = Note.objects.get(id=self.note.id+1)
        expected_slug = slugify(self.form_data['title'])
        assert new_note.slug == expected_slug


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author = User.objects.create(username='Не автор')
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )
        cls.success_url = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, self.form_data)
        assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_not_author_cant_edit_note(self):
        response = self.not_author_client.post(self.edit_url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        notes_in_db_before_del = Note.objects.count()
        response = self.author_client.post(self.delete_url)
        assertRedirects(response, self.success_url)
        notes_in_db = Note.objects.count()
        self.assertEqual(notes_in_db, notes_in_db_before_del-1)

    def test_not_author_cant_delete_note(self):
        notes_in_db_before_del = Note.objects.count()
        response = self.not_author_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_in_db = Note.objects.count()
        self.assertEqual(notes_in_db, notes_in_db_before_del)
