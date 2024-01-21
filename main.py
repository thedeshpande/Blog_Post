from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_gravatar import Gravatar
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
# from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from schema import db, BlogPost, User, Comments
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ckeditor
from dotenv import dotenv_values
from smtplib import SMTP


env = dotenv_values()

app = Flask(__name__)
app.config['SECRET_KEY'] = env['FLASK_KEY']
ckeditor.init_app(app)
Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar()
gravatar.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()


# def admin_only(func):
#     @wraps(func)
#     def decorated_function(*args, **kwargs):
#         if current_user.id == 1:
#             return func(*args, **kwargs)
#         return abort(403)
#     return decorated_function


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = env['SQL_URI']
db.init_app(app)


with app.app_context():
    db.create_all()


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email == form.email.data)).scalar():
            flash("Account on this email already exists")
            return redirect(url_for('login'))
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data, 'pbkdf2:sha256', 8)
        )
        db.session.add(user)
        db.session.commit()
        if login_user(user):
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user and check_password_hash(user.password, form.password.data):
            if login_user(user):
                return redirect(url_for('get_all_posts'))
        flash("Incorrect Credentials")
        return render_template('login.html', form=form)
    return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Kindly login to comment on a blog')
            return redirect(url_for('login'))
        comment = Comments(
            text=form.comment.data,
            author=current_user,
            blog=requested_post
        )
        db.session.add(comment)
        db.session.commit()
        return render_template('post.html', post=requested_post, form=form)
    return render_template("post.html", post=requested_post, form=form)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    if post.author_id != current_user.id:
        return abort(403)

    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@login_required
# @admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    if post_to_delete.author_id != current_user.id:
        return abort(403)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=['POST', 'GET'])
def contact():
    if request.method == 'POST':
        body = (f"Subject:You are being contacted!!!\n\n"
                f"Name: {request.form['name']}\n"
                f"Email: {request.form['email']}\n"
                f"Mobile: {request.form['phone']}\n"
                f"Message: {request.form['message']}")
        with SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(user=env['SENDER_EMAIL'], password=env['SENDER_PASSWORD'])
            connection.sendmail(from_addr=env['SENDER_EMAIL'], to_addrs=env['RECEIVER_EMAIL'], msg=body)

        flash('Your message has been shared us!')
        return render_template('contact.html')
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=False)
