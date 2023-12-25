from app import app, db
from flask import render_template, request, redirect, url_for, flash, session
from app.models import Student, Project, Task, Link, project_students, Comment, User
from datetime import datetime
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from sqlalchemy import delete

#Notes:
# each time I commit to database, i should have try, except, rollback, flash
# each time I delete I should confirm with the user like in tasks

# Home Page
@app.route("/", methods=["GET"])
def index():
    projects = Project.query.all()
    return render_template("index.html", projects=projects)

# Home Page
# Note: Will need to refactor and make this the final route for the home page and replace index route
@app.route("/", methods=["GET"])
def home():
  projects = Project.query.all()
  return render_template("index.html", projects=projects)

# Student Detail Page
# Shows the student details and projects for a student
# Public Page
@app.route("/student/<int:id>", methods=["GET"])
def student_detail(id):
    student = Student.query.get_or_404(id)
    return render_template("student_details.html", student=student)

# User Detail Page
# Shows the user details and projects for a user
# Private Page
@app.route("/user/<int:id>", methods=["GET"])
@login_required
def user_detail(id):
    user = User.query.get_or_404(id)
    return render_template("user_details.html", user=user)

## ADMIN ROUTES ##  ADMIN ROUTES ##  ADMIN ROUTES ##  ADMIN ROUTES ##  ADMIN ROUTES ##  ADMIN ROUTES ## 
# Admin Dashboard
# Shows Student Name, username, role, email, profile and projects
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():

    if not current_user.role or current_user.role.name != 'admin':
        # Redirect non-admin users or show an error message
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

## Auth Routes ##  Auth Routes ##  Auth Routes ##  Auth Routes ##  Auth Routes ##  Auth Routes ##
# Login Page
# Currently Defaults to Login into Dev User
@app.route('/login', methods=['GET', 'POST'])
def login():
    ## Remove this before production, just short way to login
    config = 'development'
    if config=='development':
        dev_user = User.query.get(1)  # Assuming user with ID 1 is your dev user
        login_user(dev_user)
        return redirect(url_for('home'))
     
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        user.role_id = 'user'
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html')

# Create User Page
# Allows Admin to create a new user
@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    # Checks admin, Only admin can create users
    if not current_user.role.name == 'admin': 
        return "Access denied", 403

    # if post request, gather data from form and create user
    if request.method == 'POST':
        # Form Data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        # Function to add a student to the project
        def add_student(first_name, last_name):
            student = Student(first_name=first_name.strip(), last_name=last_name.strip())
            student.user_id = user.id
            student.user=user
            db.session.add(student)
            db.session.flush()  # Ensure the student gets an ID if it's a new entry
            return student

        # Create new user and set password
        user = User(username=username)
        user.set_password(password)
        user.email = email
        user.role_id = role
        user.role.name=role
        student=add_student(first_name, last_name)
        user.student=student
        db.session.add(user)
        db.session.commit()

        # Redirect to login page after successful signup
        return redirect(url_for('login'))

    return render_template('create_user.html')

# Signup Page
# Allows a user to signup for an account - Currently not in use as I want to limit sign ups to admin and my students
# Note: If I bring this back, will need to add more fields to the form
@app.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    # Checks admin, Only admin can create users
    if not current_user.role.name == 'admin': 
        return "Access denied", 403
    
    # if post request, gather data from form and create user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Create new user and set password
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Redirect to login page after successful signup
        return redirect(url_for('login'))

    return render_template('signup.html')

# Logout Page
# Logs out the user and redirects back to the home page
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

## Project Routes ##  Project Routes ##  Project Routes ##  Project Routes ##  Project Routes ##  Project Routes ##
# Project Detail Page
# Shows the project details and tasks for a project
@app.route("/project/<int:id>", methods=["GET"])
def project_detail(id):
    project = Project.query.get_or_404(id)
    tasks = Task.query.filter_by(project_id=id).all()  # Fetch tasks for this project
    return render_template("project_details.html", project=project, tasks=tasks)

# Create Project Page
# Allows a user to create a new project with just a project name
# Note: Might need another route for a more complex create_project page
@app.route("/create_project", methods=["POST"])
@login_required
def create_project():
    name = request.form["title"]

    # Create a new project
    project = Project(name=name)

    # Default Values
    project.progress = 0
    priority = 1

    # Add the project to the database
    db.session.add(project)
    db.session.commit()

    project_detail_url = url_for('project_detail', id=project.project_id)

    # HTML Response Linked to project_manager.html
    response = f"""
    <tr>
       <td><a href="{project_detail_url}">{project.name}</a></td>
        <td>
            <button hx-delete="project/delete/{project.project_id}" class="btn btn-danger">
                Delete
            </button>
        </td>
    </tr>
    """
    return response
# Update Project
# Updates a project based on the project_id
# Linked to the edit button on the project details page
@app.route("/project/update/<int:id>", methods=["POST"])
@login_required
def update_project(id):
    project = Project.query.get_or_404(id)

    try:
        # Update project's attributes based on form data
        project.name = request.form.get('name')
        project.overview = request.form.get('overview')
        project.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d') if request.form.get('due_date') else None
        priority = request.form.get('priority', type=int)
        # Validate priority: should be an integer between 1 and 5
        if priority is not None:
            if not 1 <= priority <= 5:
                flash('Priority must be an integer between 1 and 5', 'error')
                return redirect(url_for('project_detail', id=id))
            else:
                project.priority = priority

        progress = request.form.get('progress', type=int)
        # Validate progress: should be an integer between 0 and 100
        if progress is not None:
            if not 0 <= progress <= 100:
                flash('Progress must be an integer between 0 and 100', 'error')
                return redirect(url_for('project_detail', id=id))
            else:
                project.progress = progress
        

        project.short_description = request.form.get('short_description')

        # Save changes to the database
        db.session.commit()
    except Exception as e:
        # Handle errors and roll back any changes
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    # Redirect to a page (e.g., project detail page) or return a response
    return redirect(url_for('project_detail', id=id))

# Update Project Overview
# Updates a project overview based on the project_id
# Linked to the edit button on the project details page
# Separate button than the update project button
@app.route("/project/update_project_overview/<int:project_id>", methods=["GET", "POST"])
@login_required
def update_project_overview(project_id):
    project = Project.query.get_or_404(project_id)

    # If the request is a GET, return the edit form
    if request.method == "GET":
        edit_form_html = f"""
        <div id="overview-container">
            <form hx-post="{url_for('update_project_overview', project_id=project.project_id)}"
                hx-trigger="submit"
                hx-target="#overview-container"
                hx-swap="outerHTML">
                <textarea id="overview" name="overview" rows="6" cols="50">{project.overview}</textarea>
                <button type="submit" class="btn btn-primary">Update Overview</button>
            </form>
        </div>
        """

        return edit_form_html
    else:
        try:
            project.overview = request.form.get("overview")
            db.session.commit()

            # HTML Response Linked to project_details.html
            return f"""
            <div id="overview-container" style="position: relative; min-height: 150px;">
                <p id="project-overview">{ project.overview }</p>
            </div>
        """
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')
            return '', 500  # HTTP 500 for server error

# Delete Project
# Deletes a project based on the project_id
# Note: Will need to add a check to make sure the user is the owner of the project
# Note: Will change route to /project/delete/<int:id>
@app.route("/project/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_project(id):
    #Checks to see if the user is the admin
    if not current_user.role.name == 'admin':
        return "Access denied", 403

    project = Project.query.get_or_404(id)
    try:
        # Manually delete related rows in project_students
        db.session.execute(delete(project_students).where(project_students.c.project_id == id))
        
        db.session.delete(project)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the project: {e}', 'danger')

    return ""

## Task Routes ##  Task Routes ##  Task Routes ##  Task Routes ##  Task Routes ##  Task Routes ##
# Add Task to Project
# Adds a task to a project based on the project_id
# Linked to the add task button on the project details page
@app.route("/project/<int:project_id>/add_task", methods=["POST"])
@login_required
def add_task(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        new_task = Task(
            name=request.form.get("task_name"),
            description=request.form.get("task_description"),
            progress = 0,
            priority = 1,
            project_id=project.project_id
        )

        db.session.add(new_task)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while adding the task: {e}', 'danger')

    return redirect(url_for('project_detail', id=project_id))

# Update Task
# Updates a task based on the task_id
# Allows all users to update a task
@app.route("/task/update/<int:task_id>", methods=["GET", "POST"])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    project = Project.query.get_or_404(task.project_id)

    # If the request is a GET, return the edit form
    if request.method == "GET":
        
        # HTML Response Linked to project_details.html Add New Task Button
        # This form calls this function again with a POST request to update instead of add_task
        edit_form_html = f"""
            <form action="{ url_for('update_task', task_id=task.task_id) }" method="post">
                <label for="task_name">Task Name:</label>
                <input type="text" id="task_name" name="task_name" />

                <label for="task_description">Description:</label>
                <input type="text" id="task_description" name="task_description" />

                <button type="submit" class="btn btn-primary">Add Task</button>
            </form>
        """
        return edit_form_html

    # If the request is a POST, update the task
    elif request.method == "POST":
        try:
            # Update task's attributes based on form data
            task.name = request.form.get("task_name")
            task.description = request.form.get("task_description")
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating the task: {e}', 'danger')

        # After updating the task, redirect to the project detail page
        return redirect(url_for('project_detail', id=task.project_id))

# Delete Task
# Deletes a task based on the task_id
@app.route("/task/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the task: {e}', 'danger')

    return ""
## Link Routes ##  Link Routes ##  Link Routes ##  Link Routes ##  Link Routes ##  Link Routes ##
# Add Link to Project
# Adds a link to a project based on the project_id
# Note: I don't really understand this route and how the links currently get updated without reload.
# Potentially could switch to a pure htmx solution, but right now it works
@app.route("/add_link", methods=["POST"])
@login_required
def add_link():
    try:
        # Creates a link based on the form data including the project_id via hidden input
        new_link = Link(
            url=request.form.get("url"),
            project_id=request.form.get("project_id", type=int),
            task_id=request.form.get("task_id", type=int)
        )

        db.session.add(new_link)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while adding the link: {e}', 'danger')

    return redirect(request.referrer or url_for('home'))

# Cancel Edit Link
# Cancels the edit link form and returns the link to the original state
@app.route("/cancel_edit_link/<int:link_id>", methods=["GET"])
@login_required
def cancel_edit_link(link_id):
    link = Link.query.get_or_404(link_id)

    # HTML Response Linked to project_details.html Link Edit/Delete Buttons
    return f'''
    <li hx-swap="outerHTML" id="link-{link.id}">
        <a href="{link.url}" target="_blank">{link.url}</a>
        <button hx-get="{url_for('update_link', link_id=link.id)}" class="btn btn-xs btn-primary">Edit</button>
        <button hx-post="{url_for('delete_link', link_id=link.id)}" hx-confirm="Are you sure you want to delete this link?" hx-target="closest li" hx-swap="outerHTML" class="btn btn-xs btn-danger">Delete</button>
    </li>
    '''
# Update Link
# Updates a link based on the link_id and get and post methods
@app.route("/update_link/<int:link_id>", methods=['GET', 'POST'])
@login_required
def update_link(link_id):
    link = Link.query.get_or_404(link_id)
    
    # If the request is a GET, return the edit form
    if request.method == 'GET':
        # HTML Response Linked to project_details.html Link Edit/Delete Buttons
        response = f"""
        <form hx-post="{url_for('update_link', link_id=link.id)}" hx-swap="outerHTML" id="link-{link.id}">
            <input type="hidden" name="project_id" value="{link.project_id}">
            <input type="text" name="url" value="{link.url}" placeholder="Edit URL">
            <button type="button" hx-get="{url_for('cancel_edit_link', link_id=link.id)}" hx-target="#link-{link.id}" hx-swap="outerHTML" class="btn btn-xs btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-xs btn-primary">Save</button>
        </form>
        """
        return response
    else:
        try:
            new_url = request.form.get("url")

            link.url = new_url
            db.session.commit()

            # HTML Response Linked to project_details.html Link Edit/Delete Buttons
            updated_link_html = f"""
                <li id="link-{ link.id }">
                    <a href="{ link.url}" target="_blank">{ link.url }</a>
                        <button hx-get="{ url_for('update_link', link_id=link.id) }"
                                hx-target="#link-{ link.id }"
                                hx-swap="outerHTML"
                                class="btn btn-xs btn-primary">Edit</button>

                        <button hx-post="{ url_for('delete_link', link_id=link.id) }"
                                hx-confirm="Are you sure you want to delete this link?"
                                hx-target="closest div"
                                hx-swap="outerHTML"
                                class="btn btn-xs btn-danger">Delete</button>
                </li>
            """
            return updated_link_html
        except (Exception) as e:
            db.session.rollback()
            return f"<div>Error: {e}</div>", 500

# Delete Link
# Deletes a link based on the link_id
@app.route("/delete_link/<int:link_id>", methods=["POST"])
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    try:
        db.session.delete(link)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the link: {e}', 'danger')

    return ""

## Comment Routes ##  Comment Routes ##  Comment Routes ##  Comment Routes ##  Comment Routes ##  Comment Routes ##
# Add Comment to Project
# Adds a comment to a project based on the project_id
# Note: Currently when you add a new comment, the edit and delete buttons will show up no matter what. Right now that is intended
@app.route('/add-comment/<int:project_id>', methods=['POST'])
@login_required
def add_comment(project_id):
    # Create a new comment based on the form data
    new_comment_text = request.form.get('comment_text')
    new_comment = Comment(text=new_comment_text, project_id=project_id)

    # Add the comment to the database
    db.session.add(new_comment)
    db.session.commit()

    # HTML Response Linked to project_details.html Add New Comment Button
    comments_html = f"""
            <div id="comment-{new_comment.comment_id}" class="col-3">
                <div class="card">
                    <div class="card-body">
                        <p class="card-text">{new_comment.text}</p>
                        <!-- Edit Button -->
                        <button hx-get="{ url_for('edit_comment_form', comment_id=new_comment.comment_id) }" 
                                hx-target="#comment-{new_comment.comment_id}" 
                                class="btn btn-primary btn-sm">Edit</button>
                        <!-- Delete Button -->
                        <button hx-post="{ url_for('delete_comment', comment_id=new_comment.comment_id) }" 
                                hx-target="#comment-{new_comment.comment_id}" 
                                class="btn btn-danger btn-sm">Delete</button>
                    </div>
                </div>
            </div>
        """
    return comments_html

# Edit Comment Form
# Edits a comment based on the comment_id
# Note: Doesn't check to see if the user is the owner of the comment
@app.route('/edit-comment-form/<int:comment_id>')
@login_required
def edit_comment_form(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # HTML to edit the comment
    edit_form_html = f"""
        <form method='POST' hx-post='{url_for("update_comment", comment_id=comment.comment_id)}' hx-target='#comment-{comment.comment_id}'>
            <textarea name='comment_text'>{comment.text}</textarea>
            <button type='submit' class="btn btn-sm btn-primary">Update Comment</button>
        </form>
    """
    return edit_form_html

@app.route('/update-comment/<int:comment_id>', methods=['POST'])
@login_required
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.text = request.form.get('comment_text')
    db.session.commit()

    updated_comment_html = f"""
        <div id="comment-{comment.comment_id}">
            <p>{comment.text}</p>
            <button hx-get='{url_for('edit_comment_form', comment_id=comment.comment_id)}' hx-target="#comment-{comment.comment_id}" class="btn btn-primary">Edit</button>
            <button hx-post='{url_for('delete_comment', comment_id=comment.comment_id)}' hx-target="#comment-{comment.comment_id}" class="btn btn-danger">Delete</button>
        </div>
    """
    return updated_comment_html

@app.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    project_id = comment.project_id
    db.session.delete(comment)
    db.session.commit()

    project = Project.query.get_or_404(project_id)
    comments_html = ""
    return comments_html

@app.route('/toggle_special_functionality/<int:project_id>', methods=['POST'])
@login_required
def toggle_special_functionality(project_id):
    # Assume get_project_by_id is a function that returns a project object
    project = Project.query.get_or_404(project_id)
    
    # Toggle the special functionality state in the session
    session_key = f'special_functionality_{project_id}'
    special_functionality_enabled = session.get(session_key, False)
    session[session_key] = not special_functionality_enabled

    # Render and return the full page (or the part of the page you want to swap)
    return render_template('project_details.html', project=project, special_functionality_enabled=session[session_key])

@app.route('/admin/link-users', methods=['GET', 'POST'])
@login_required
def admin_link_users():
    if not current_user.role.name == 'admin': 
        return "Access denied", 403

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        student_id = request.form.get('student_id')

        # Find the user and student from the database
        user = User.query.get(user_id)
        student = Student.query.get(student_id)

        if user and student:
            # Link the student to the user
            student.user_id = user.id
            db.session.commit()
            print(f'Successfully linked User ID: {user_id} with Student ID: {student_id}.')
            return redirect(url_for('admin_link_users'))
        else:
            print("User or Student not found.")

    # On GET, render a template with forms to create new links
    users = User.query.all()  # Or some filtering if your user list is large
    students = Student.query.all()
    return render_template('admin_link_users.html', users=users, students=students)

@app.route('/chat', methods=['GET'])
def chat():
    return render_template('chat.html')

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    user_query = request.form['query']
    # openai.api_key = os.getenv('OPENAI_API_KEY')
    # response = openai.Completion.create(engine="davinci", prompt=user_query, max_tokens=150)
    # bot_response = response.choices[0].text.strip()
    bot_response = "Hello, this is just for testing."
    # Create a multi-part response
    chat_response = f'<div>{user_query}: {bot_response}</div>'
    clear_input_script = '<script>document.getElementById("userQuery").value = "";</script>'
    
    # Combine the chat response and the script to clear the input field
    combined_response = chat_response + clear_input_script
    return combined_response

@app.route('/project_manager')
def project_manager():
    projects = Project.query.all()
    return render_template('project_manager_page.html', projects=projects)