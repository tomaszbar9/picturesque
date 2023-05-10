# PICTURESQUE

#### Video Demo: https://youtu.be/95eBI367RwE

---

### \*\*\*UPDATE\*\*\*

The Picutresque website is my final project for the Harvard University course CS50: Introduction to Computer Science. Later, I have written anew the whole backend side of an application based on the same idea, but this time I used Flask-Smorest framework and tried to create a proper REST API. The repository of the new application is [here](https://github.com/tomaszbar9/picturesque_api).

---

#### Description:

The project was inspired by W.G. Sebald who used to beef his books up with photos of described places. It is a website that allows of creating a kind of blog that matches quotes from world literature with relative pictures. It is also possible to mark referred places on the map. If populated, the database created via the website would be a nice way not only to get more familiar with the places from our favourite books but also, thanks to divers ways to browse the database, to get to know new works of literature.

To view the posts, a user can enter the “All posts” link and then choose a type of sorting. The posts can be ordered by dates (from the latest or from the oldest), popularity, authors, and titles.

One can also use the search bar on the homepage to look for posts containing a specific phrase.

From a post window, if the post was marked, the user can enter the map and there find other posts’ markers that also work as links. It is possible to toggle between all markers and the ones related to the specific book. This way, for example, the user can browse posts that were located in a town they are interested in.

Once registered, the user can add other people’s posts to the collection. The program uses collections to create recommendations for each user. The mechanism is pretty simple. Let’s say the program is making the recommendations for a user named Machiavelli. First, it looks for other users who have the same posts added to their collections as Machiavelli. Then it selects from these collections the posts that weren’t chosen or created by him, and adds them to the list of the recommended posts. Next, each post has assigned points, and the number of the points depends on the similarity of the collection it is coming from to the Machiavelli’s collection. For example, if Beckham has 9 posts in common with Machiavelli, any other of Beckham’s posts will get 9 points each. The post displayed first on the Machiavelli’s “Recommendations” site is the one that gathered the highest number of points.

The website’s backend is written in Python 3.6, using the Flask framework.

The database is managed with Flask-SQLAlchemy using Object Relational Mapper.

Thanks to the Flask-admin library, it is possible to access the database’s graphical interface simply by entering the “admin” route.

The Pillow module is used to compress and save the photos.

The GeoPy module is used to locate a place’s name entered by a user during a post’s creation, and later to look for a search phrase in the database. Thanks to it, a user while searching can enter a place’s name in almost any language. Before comparing with the database, the phrase is translated by GeoPy to match the names stored in the “Place” column.

The frontend is written in HTML, CSS, JavaSript and Jinja. Although it works, I am fully aware that it could have been written much better, but at this stage I’ve just decided to focus on learning and practicing one language, i.e. Python.

Since the database, as it is, is almost empty, to facilitate testing the website I have included an independent script “populate.py” that, not surprisingly, populates the database with dummy posts. For the sake of testing, I took the liberty of using 50 photos that come from the “Recovery” project, CS50 Problem Set 4. For the beginning, the database contains only ten titles of books by five authors, and six users. The first user’s name is Alice, and all of them have the same password: “q1111111”. The program takes the files from the “cs50_photos” folder and assign each of them to random title and user. As a quote it pastes a few lines of “Lorem ipsum”, but before the quote is saved, a “keyword” is pasted somewhere into it. The keywords list is created from the authors’ names, titles and users’ names. This way it is possible that the searching returns some of the quotes too. There is also a 33% chance that the post will be marked on the map. The program generates random coordinates for the lucky post, placing it somewhere in Dublin. So, in order to test the Pictureque website, run the “populate.py” script first.

#### Folders and Files:

- **app.py**: The core of the website. Every block is described in the comments.
- **base.db**: Database with the tables: Users, Authors, Titles, Posts, Favorites.
- **config.py**: Script with the configuration data, imported by other scripts as the Config object.
- **database.py**: Each table’s class definition.
- **helpers.py**: Auxiliary functions.
- **populate.py**: Described in above in the “Description” section.
- **requirements.py**: List of used modules.
- **cs50_photos**: Small photos for the testing purpose.
- **static**
  - **photos**: Directory for the photos.
  - **quotes**: Directory for the quotes.
  - **thumbnails**: Directory for the thumbnails.
  - **script.js**: JavaScript functions used by the HTML files: “login”, “register”, and “new_entry” to validate a user’s input. The functions verify the forms and if the input is invalid, block posting the request to the server and display a relevant alert. Every input is double-checked. If for any reason the user tries to override the client-side validation, the form will be sent to them again also with an alert.
  - **styles.css**: Stylesheet for the HTML files.
  - Beside the folders and the files listed above, 'static' contains also three image files with favicon, home button image, and the photography used as the homepage's background (unfortunately I do not know the name of the author).
- **templates**
  - **admin**: Directory used by Flask-admin module.
  - **help.html**: Auxiliary file for other HTML files. Contains jinja macro required to display the pagination bar.
  - **index.html**: Homepage.
  - **layout_log.html**: Template for the pages without the navigation bar and background: “login” and “register”
  - **layout_main.html**: Template for all the other pages.
  - **layout.html**: Template for both above templates.
  - **login.html**: Log-in form.
  - **new_entry.html**: New post uploader. The page is also used to modify an existing post.
  - **post.html**: Page displaying a single post. Used also to place a marker on the map.
  - **posts.html**: Page displaying a portion of many posts, be it all of them or just a single user’s posts. It allows a few types of sorting.
  - **register.html**: Register form.
  - **search.html**: Page showing a search outcome. The section with the most results is displayed first. The bookmarks help the user to navigate between sections.
