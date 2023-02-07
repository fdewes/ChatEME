init:
	./manage.py makemigrations
	./manage.py migrate
	./manage.py createsuperuser --noinput --username admin --email admin@example.com 

clean:
	rm db.sqlite3
	rm ChatEME/migrations/0*
	rm -rf ChatEME/__pycache__
	rm -rf __pycache__
