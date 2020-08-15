#forms.py

from wtforms import Form, StringField, SelectField

class BookSearchForm(Form):
	choices = [('Title', 'Title'), ('Author', 'Author'), ('ISBN', 'ISBN')]
	select = SelectField('Search for books:', choices=choices)
	search = StringField('')

