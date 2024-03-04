import subprocess

from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from datetime import date
import os
from pathlib import Path

app = Flask(__name__)

# Database connection
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='Srihari@2003',
    database='dbms_proj'
)

cursor = conn.cursor()


# Routes
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        userCount = 0
        with open('user_count.txt', 'r') as f:
            userCount = int(f.readline())
        # Insert the user into the database
        cursor.execute(
            'INSERT INTO user (user_name, email, password, user_id, date_joined) VALUES (%s, %s, %s, %s, %s)',
            (username, email, password, f'{username[:2]}{userCount:04d}', date.today().strftime('%Y-%m-%d')))
        conn.commit()

        with open('user_count.txt', 'w') as f:
            f.write(f'{userCount + 1}')

        return redirect('/login')

    return render_template('signup.html')


@app.route('/authenticate', methods=['POST'])
def authenticate():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(email, password)
        # Check user credentials in the employee table
        cursor.execute(
            'SELECT distinct e.email, e.password '
            'FROM employee e '
            'JOIN department d ON e.emp_id = d.mgr_id '
            'WHERE e.email=%s AND e.password=%s',
            (email, password))
        emp = cursor.fetchall()
        if emp:
            cursor.execute('SELECT DISTINCT e.emp_id, e.emp_address, e.emp_name, e.emp_age, e.emp_dob, '
                           'e.emp_sal, e.emp_posn, e.skills, e.email, e.password '
                           'FROM employee e '
                           'JOIN department d ON e.emp_id = d.mgr_id '
                           'WHERE e.email=%s AND e.password=%s',
                           (email, password))
            mgr = cursor.fetchone()
            return redirect(url_for('manager', user_data=mgr))

        cursor.execute('SELECT DISTINCT e.emp_id, e.emp_address, e.emp_name, e.emp_age, e.emp_dob, '
                       'e.emp_sal, e.emp_posn, e.skills, e.email, e.password '
                       'FROM employee e '
                       'WHERE e.email=%s AND e.password=%s', (email, password))
        emp = cursor.fetchone()
        if emp:
            return redirect(url_for('employee', user_data=emp))
        else:
            # Check user credentials in the users table
            cursor.execute('SELECT * FROM user WHERE email=%s AND password=%s', (email, password))
            user = cursor.fetchone()
            if user:
                return redirect(url_for('user', user_data=user))
            else:
                return redirect('/login?x=True')

    return redirect('/login')


# TODO 1: Entry Pages
@app.route('/manager')
def manager():
    # Fetch manager-specific data from the database
    user_data = request.args.get('user_data')
    cursor.execute('SELECT emp_name from employee where emp_id = %s', (user_data,))
    name = cursor.fetchone()
    return render_template('manager.html', user_data=user_data, name=name)


@app.route('/employee')
def employee():
    # Fetch employee-specific data from the database
    user_data = request.args.get('user_data')
    cursor.execute('SELECT emp_name from employee where emp_id = %s', (user_data,))
    name = cursor.fetchone()
    return render_template('employee.html', user_data=user_data, name=name)


@app.route('/user')
def user():
    # Fetch employee-specific data from the database
    user_data = request.args.get('user_data')
    cursor.execute('SELECT user_name from user where user_id = %s', (user_data,))
    name = cursor.fetchone()
    return render_template('user.html', user_data=user_data, name=name)


# TODO 2: Profile Pages
@app.route('/profile_emp')
def profile_emp():
    user_data = request.args.get('user')
    print(user_data)
    cursor.execute('SELECT * FROM employee WHERE emp_id=%s', (user_data,))
    data = cursor.fetchall()
    print(data)
    return render_template('profile_emp.html', user_data=data[0])


@app.route('/profile_usr')
def profile_usr():
    user_data = request.args.get('user')
    print(user_data)
    cursor.execute('SELECT * FROM user WHERE user_id=%s', (user_data,))
    data = cursor.fetchall()
    print(data)
    return render_template('profile_usr.html', user_data=data[0])


# TODO 3: Tables for management

@app.route('/users_managed')
def users_managed():
    # Fetch users managed by the employee from the database
    emp_id = request.args.get('user')
    cursor.execute(
        'SELECT d.user_name, d.user_id, d.date_joined, d.email '
        'FROM employee e '
        'JOIN emp_user ed ON e.emp_id = ed.emp_id '
        'JOIN user d ON ed.user_id = d.user_id '
        'WHERE e.emp_id = %s', (emp_id,))
    users_managed = cursor.fetchall()
    print(users_managed)
    return render_template('users_managed.html', users_managed=users_managed)


@app.route('/employees_managed')
def employees_managed():
    # Fetch employees managed by the manager from the database
    mgr_id = request.args.get('user')
    cursor.execute(
        'SELECT DISTINCT e.emp_id, e.emp_name, e.email '
        'FROM employee e '
        'JOIN emp_dept ed ON e.emp_id = ed.emp_id '
        'JOIN department d ON ed.dept_id = d.dept_id '
        'WHERE d.mgr_id = %s', (mgr_id,))
    emp_managed = cursor.fetchall()
    return render_template('employees_managed.html', emp_managed=emp_managed)


@app.route('/projects_managed')
def projects_managed():
    # Fetch projects managed by the employee from the database
    emp_id = request.args.get('user_data')
    cursor.execute(
        'SELECT p.proj_id, p.proj_name, p.proj_status, ep.proj_start '
        'FROM project p, emp_proj ep '
        'where p.proj_id = ep.proj_id '
        'and ep.emp_id = %s', (emp_id,))
    projects_managed = cursor.fetchall()
    return render_template('projects_managed.html', projects_managed=projects_managed)


# TODO 4: Department Details

@app.route('/dept_details')
def dept_details():
    # Fetch department details from the database
    curr_emp_id = request.args.get('user')
    print(curr_emp_id)
    cursor.execute('SELECT d.* FROM department d JOIN emp_dept ed ON d.dept_id = ed.dept_id WHERE ed.emp_id = %s',
                   (curr_emp_id,))
    dept_details = cursor.fetchall()
    print(dept_details)
    return render_template('dept_details.html', dept_details=dept_details)


# TODO 5: Download Page

# Route for the downloads page
@app.route('/download', methods=['POST', 'GET'])
def download():
    if request.method == 'POST':
        user_data = request.args.get('user')
        cursor.execute('SELECT g.game_name, g.version, g.repo_id, b.branch_location '
                       'FROM game g '
                       'JOIN game_at_branch gab ON g.game_id = gab.game_id '
                       'JOIN branch b ON gab.branch_id = b.branch_id')
        games = cursor.fetchall()
        game_id = request.form.get('game_id')
        print(game_id)
        subprocess.run(['git', 'clone', game_id])
        repo_name = game_id.split('/')[-1].split('.')[0]  # Extract Folder name
        os.startfile(f'{repo_name}')
        return redirect(url_for('download', games=games, user_data=user_data, success='dtrue'))

    user_data = request.args.get('user')
    cursor.execute('SELECT g.game_name, g.version, g.repo_id, b.branch_location '
                   'FROM game g '
                   'JOIN game_at_branch gab ON g.game_id = gab.game_id '
                   'JOIN branch b ON gab.branch_id = b.branch_id')
    games = cursor.fetchall()
    return render_template('download.html', games=games, user_data=user_data)


# Route for adding a review
@app.route('/add_review', methods=['POST'])
def add_review():
    if request.method == 'POST':
        # Get review details from the form
        game_name = request.form['game_name']
        user_id = request.form['user_id']
        rating = request.form['rating']
        comment = request.form['comment']
        # Find the game ID
        cursor.execute('SELECT game_id FROM game WHERE game_name=%s', (game_name,))
        game_id = cursor.fetchone()[0]

        # Read review count from file
        review_count = 0
        with open('rev_count.txt', 'r') as f:
            review_count = int(f.read())

        # Generate review ID
        review_id = int(f'{review_count + 100}')

        try:
            # Insert review into the database
            cursor.execute('INSERT INTO review (rev_id, rating, comment, rev_date) VALUES (%s, %s, %s, %s)',
                           (review_id, rating, comment, date.today().strftime('%Y-%m-%d')))
            conn.commit()
            # Update user_game and game_review tables
            cursor.execute('INSERT INTO user_game (user_id, game_id) VALUES (%s, %s)', (user_id, game_id))
            cursor.execute('INSERT INTO game_review (game_id, rev_id) VALUES (%s, %s)', (game_id, review_id))
            conn.commit()
        except mysql.connector.errors.IntegrityError:
            conn.rollback()
            return redirect(url_for('download', user=user_id, success='false'))

        # Update review count in the file
        with open('rev_count.txt', 'w') as f:
            f.write(str(review_count + 100))

        # Redirect back to the downloads page
        return redirect(url_for('download', user=user_id, success='true'))


# Add the route for the "reviews_added" page
@app.route('/reviews_added')
def reviews_added():
    user_id = request.args.get('user')
    print(user_id)
    # Fetch all reviews added by the user from the database
    cursor.execute('SELECT r.rev_id, r.rating, r.comment, r.rev_date, g.game_name '
                   'FROM review r '
                   'JOIN game_review gr ON r.rev_id = gr.rev_id '
                   'JOIN user_game ug ON gr.game_id = ug.game_id '
                   'JOIN game g ON ug.game_id = g.game_id '
                   'WHERE ug.user_id = %s', (user_id,))
    reviews = cursor.fetchall()
    return render_template('reviews_added.html', reviews=reviews)


# TODO EDITING Data

# Flask routes for editing and adding users and employees
@app.route('/edit_user', methods=['GET', 'POST'])
def edit_user():
    if request.method == 'POST':
        # Process form submission to edit user
        user_id = request.form['user_id']
        new_name = request.form['username']
        new_email = request.form['email']
        password = request.form['password']
        # Update user in the database using user_id
        cursor.execute('UPDATE user SET user_name = %s, email = %s, password=%s WHERE user_id = %s',
                       (new_name, new_email, password, user_id))
        conn.commit()

        print(user_id)
        cursor.execute(
            'SELECT e.emp_id '
            'FROM employee e '
            'JOIN emp_user ed ON e.emp_id = ed.emp_id '
            'JOIN user d ON ed.user_id = d.user_id '
            'WHERE d.user_id = %s', (user_id,))
        emp_id = cursor.fetchone()[0]
        print(emp_id)
        return redirect(f'/users_managed?user={emp_id}')

    # Handle GET request to display edit form
    user_id = request.args.get('username')
    print(user_id)
    cursor.execute('SELECT * FROM user WHERE user_id = %s', (user_id,))
    user_details = cursor.fetchone()
    print(user_details)
    return render_template('edit_user.html', user_data=user_details)


@app.route('/edit_employee', methods=['GET', 'POST'])
def edit_employee():
    if request.method == 'POST':
        # Process form submission to edit employee
        emp_id = request.form['emp_id']
        print(emp_id)
        new_name = request.form['name']
        new_email = request.form['email']
        # Update employee in the database using emp_id
        cursor.execute('UPDATE employee SET emp_name = %s, email = %s WHERE emp_id = %s',
                       (new_name, new_email, emp_id))
        conn.commit()

        cursor.execute(
            'SELECT d.mgr_id FROM employee e '
            'JOIN emp_dept ed ON e.emp_id = ed.emp_id '
            'JOIN department d ON ed.dept_id = d.dept_id '
            'WHERE e.emp_id = %s', (emp_id,))
        emp_id = cursor.fetchone()[0]
        print(emp_id)
        return redirect(f'/employees_managed?user={emp_id}')

    # Handle GET request to display edit form
    emp_id = request.args.get('emp_id')
    cursor.execute('SELECT emp_id, emp_name, email FROM employee WHERE emp_id = %s', (emp_id,))
    emp_details = cursor.fetchone()
    return render_template('edit_employee.html', employee=emp_details)


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        # Retrieve form data
        emp_id = request.form['emp_id']
        emp_name = request.form['emp_name']
        emp_address = request.form['emp_address']
        emp_age = request.form['emp_age']
        emp_dob = request.form['emp_dob']
        emp_sal = request.form['emp_sal']
        emp_posn = request.form['emp_posn']
        skills = request.form['skills']
        email = request.form['email']
        password = request.form['password']
        dept_name = request.form['dept_name']  # Retrieve selected department name
        proj_name = request.form['proj_name']  # Retrieve selected project name

        # Insert new employee into the database
        cursor.execute(
            'INSERT INTO employee (emp_id ,emp_name, emp_address, emp_age, emp_dob, '
            'emp_sal, emp_posn, skills, email, password)'
            ' VALUES (%s ,%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (emp_id, emp_name, emp_address, emp_age, emp_dob, emp_sal, emp_posn, skills, email, password))
        conn.commit()

        # Retrieve department and project IDs based on the selected names
        cursor.execute('SELECT dept_id FROM department WHERE dept_name = %s', (dept_name,))
        dept_id = cursor.fetchone()[0]
        cursor.execute('SELECT proj_id FROM project WHERE proj_name = %s', (proj_name,))
        proj_id = cursor.fetchone()[0]

        # Insert employee and department association into emp_dept table
        cursor.execute('INSERT INTO emp_dept (emp_id, dept_id) VALUES (%s, %s)', (emp_id, dept_id))
        conn.commit()

        # Insert employee and project association into emp_proj table
        cursor.execute('INSERT INTO emp_proj (emp_id, proj_id) VALUES (%s, %s)', (emp_id, proj_id))
        conn.commit()

        cursor.execute(
            'SELECT d.mgr_id FROM employee e '
            'JOIN emp_dept ed ON e.emp_id = ed.emp_id '
            'JOIN department d ON ed.dept_id = d.dept_id '
            'WHERE e.emp_id = %s', (emp_id,))
        emp_id = cursor.fetchone()[0]
        print(emp_id)
        return redirect(f'/employees_managed?user={emp_id}')

    # Fetch department names for dropdown menu
    cursor.execute('SELECT dept_name FROM department')
    dept_names = [row[0] for row in cursor.fetchall()]

    # Fetch project names for dropdown menu
    cursor.execute('SELECT proj_name FROM project')
    proj_names = [row[0] for row in cursor.fetchall()]

    return render_template('add_employee.html', dept_names=dept_names, proj_names=proj_names)


@app.route('/sql_command', methods=['GET', 'POST'])
def sql_command():
    if request.method == 'POST':
        # Get the SQL command submitted by the manager
        sql_command = request.form['sql_command']

        try:
            # Execute the SQL command
            cursor.execute(sql_command)
            # Fetch the results, if any
            results = cursor.fetchall()
            return render_template('sql_command.html', results=results)
        except Exception as e:
            # Handle errors gracefully
            error_message = str(e)
            return render_template('sql_command.html', error_message=error_message)

    return render_template('sql_command.html', results=None, error_message=None)


# Flask route for adding a project by an employee
@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        # Retrieve form data
        proj_id = request.form['proj_id']
        proj_name = request.form['proj_name']
        proj_status = request.form['proj_status']
        start_date = request.form['start_date']
        duration = request.form['durn']
        emp_id = request.form['emp_id']
        print(emp_id)
        # Insert project details into the database
        cursor.execute(
            'INSERT INTO project (proj_id,  proj_name, proj_status) VALUES (%s, %s, %s)',
            (proj_id, proj_name, proj_status))
        conn.commit()

        # Update the emp_proj table to associate the employee with the project
        cursor.execute('INSERT INTO emp_proj (emp_id, proj_id, proj_start, proj_durn) VALUES (%s, %s, %s, %s)',
                       (emp_id, proj_id, start_date, duration))
        conn.commit()

        # Redirect to a page indicating success
        return redirect('/projects_managed?user_data={}'.format(emp_id))

    # If it's a GET request, render the add_project.html template
    emp_id = request.args.get('user_data')
    return render_template('add_project.html', emp_id=emp_id)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
