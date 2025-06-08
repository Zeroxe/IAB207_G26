from website import db, create_app
from website.models import Genre

app = create_app()
ctx = app.app_context()
ctx.push()
db.create_all()


def add_sample_genres():
    genres_to_add = [
        {"name": "House", "description": "House music genre"},
        {"name": "Techno", "description": "Techno music genre"},
        {"name": "Trance", "description": "Trance music genre"},
        {"name": "Drum and Bass", "description": "Drum and Bass music genre"},
        {"name": "Dubstep", "description": "Dubstep music genre"},
        {"name": "Hardstyle", "description": "Hardstyle music genre"},
        {"name": "Rave", "description": "Rave music genre"},
        {"name": "EDM", "description": "EDM music genre"},
        {"name": "Hip-Hop", "description": "Hip-Hop music genre"},
        {"name": "Instrumental", "description": "Instrumental music genre"},
        {"name": "Other", "description": "Other music genre"},
    ]

    for genre_data in genres_to_add:
        existing_genre = db.session.scalar(
            db.select(Genre).filter_by(name=genre_data["name"])
        )
        if not existing_genre:
            new_genre = Genre(
                name=genre_data["name"], description=genre_data["description"]
            )
            db.session.add(new_genre)
            print(f"Added genre: {genre_data['name']}")

    db.session.commit()


add_sample_genres()
ctx.pop()

# Quit the script
quit()
