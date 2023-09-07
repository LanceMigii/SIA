from flask import Flask, request, render_template, redirect, url_for, flash, session
import mysql.connector
import os

app = Flask(__name__)
secret_key = os.urandom(24)
app.secret_key = secret_key

# MySQL configuration (replace with your database settings)
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "jmc12345",
    "database": "SIA"
}

# Connect to the database
def connect_to_database():
    try:
        database_connection = mysql.connector.connect(**db_config)
        return database_connection
    except mysql.connector.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

# Check if a name already exists in the database
def name_exists(name, cursor):
    query = "SELECT name FROM users WHERE name = %s"
    cursor.execute(query, (name,))
    result = cursor.fetchone()
    return result is not None

#root
@app.route('/')
def index():
    return render_template('index.html')

#Click Here @index.html
@app.route('/registration')
def registration():
    return render_template('registration.html')


# Check if a name and password combination exists in the database
def is_valid_credentials(name, password, cursor):
    query = "SELECT name FROM users WHERE name = %s AND password = %s"
    cursor.execute(query, (name, password))
    result = cursor.fetchone()
    return result is not None

#login
@app.route('/webpage', methods=['GET', 'POST'])
def webpage():
    name = request.form['name']
    password = request.form['password']

    # Connect to the database
    database_connection = connect_to_database()

    if database_connection:
        try:
            cursor = database_connection.cursor()

            if is_valid_credentials(name, password, cursor):
                session['name'] = name
                return render_template('welcome.html', name=name)
            else:
                flash('Invalid username or password. Please try again.','Error')
                return redirect(url_for('index'))
        except mysql.connector.Error as e:
            print(f"Error checking credentials: {e}")
            flash('An error occurred while checking your credentials. Please try again later.', 'error')
            return redirect(url_for('index'))
        finally:
            cursor.close()
            database_connection.close()

#register
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        age = request.form['age']
        birthday = request.form['birthday']
        address = request.form['address']
        work = int(request.form.get('work', 0))

        # Connect to the database
        database_connection = connect_to_database()

        if database_connection:
            try:
                cursor = database_connection.cursor()

                if name_exists(name, cursor):
                    flash('Name already exists. Please choose a different name.', 'error')
                    return redirect(url_for('registration'))
                else:
                    query = "INSERT INTO users (name, password, age, birthday, address, work) VALUES (%s, %s, %s, %s, %s, %s)"
                    values = (name, password, age, birthday, address, work)
                    cursor.execute(query, values)
                    database_connection.commit()

                    session['name'] = name
                    return render_template('welcome.html', name = name)
            except mysql.connector.Error as e:
                print(f"Error inserting data into the database: {e}")
                flash('Error during registration. Please try again later.', 'error')
                return redirect(url_for('registration'))
            finally:
                cursor.close()
                database_connection.close()

    # Handle GET request to the registration route (render the registration form)
    return render_template('registration.html')

# Route to get user data
@app.route('/profile')
def profile():
    name = session.get('name')

    # Connect to the database
    database_connection = connect_to_database()

    if database_connection:
        try:
            cursor = database_connection.cursor()
            query = "SELECT * FROM users WHERE name = %s"
            cursor.execute(query, (name,))
            user_data = cursor.fetchone()  # Assuming there is only one user with that name

            if user_data:
                # Render a template to display the user data
                return render_template('profile.html', user_data=user_data)
            else:
                flash('User not found.', 'error')
                return redirect(url_for('webpage'))  # You may need to adjust this route
        except mysql.connector.Error as e:
            print(f"Error fetching user data: {e}")
            flash('An error occurred while fetching user data. Please try again later.', 'error')
            return redirect(url_for('webpage'))  # You may need to adjust this route
        finally:
            cursor.close()
            database_connection.close()

#Go back to the mainpage from profile
@app.route('/go_back')
def go_back():
    name = session.get('name')
    return render_template('welcome.html', name = name)

#Go to confirmation
@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

#If user choose to delete his profile from the database
@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    action = request.form.get('action')
    name = session.get('name')

    if action == 'Delete':
        database_connection = connect_to_database()

        if database_connection:
            try:
                cursor = database_connection.cursor()
                query = "DELETE FROM users WHERE name = %s"
                cursor.execute(query, (name,))
                database_connection.commit()

                # Clear the user's session data
                session.pop('name', None)

                flash('Your profile has been deleted.', 'success')
                return redirect(url_for('index'))
            except mysql.connector.Error as e:
                print(f"Error deleting user profile: {e}")
                flash('An error occurred while deleting your profile. Please try again later.', 'error')
                return redirect(url_for('profile'))
            finally:
                cursor.close()
                database_connection.close()
    elif action == 'Cancel':
        flash('Profile deletion canceled.', 'info')
        return redirect(url_for('profile'))
    return render_template('profile.html')

#edit profile
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # Connect to the database
    database_connection = connect_to_database()

    if database_connection:
        try:
            cursor = database_connection.cursor()

            # Retrieve the current user's data from the database
            name = session.get('name')
            query = "SELECT * FROM users WHERE name = %s"
            cursor.execute(query, (name,))
            user_data = cursor.fetchone()

            if request.method == 'POST':
                # Handle form submission for updating user data
                new_name = request.form['name']
                new_password = request.form['password']
                new_age = int(request.form['age'])
                new_birthday = request.form['birthday']
                new_address = request.form['address']
                new_work = int(request.form.get('work', 0))

                # Update user data in the database
                query = "UPDATE users SET name=%s, password=%s, age=%s, birthday=%s, address=%s, work=%s WHERE name=%s"
                values = (new_name, new_password, new_age, new_birthday, new_address, new_work, name)
                cursor.execute(query, values)
                database_connection.commit()

                # Update the session with the new name
                session['name'] = new_name
                flash('Profile updated successfully.', 'success')
                return redirect(url_for('profile'))
            else:
                if user_data:
                    return render_template('edit.html', user_data=user_data)
                else:
                    flash('User not found.', 'error')
                    return redirect(url_for('profile'))
        except mysql.connector.Error as e:
            print(f"Error fetching/updating user data: {e}")
            flash('An error occurred while fetching/updating user data. Please try again later.', 'error')
            return redirect(url_for('profile'))
        finally:
            cursor.close()
            database_connection.close()

    return render_template('edit.html')  # Render the edit form

#logout
@app.route('/logout')
def logout():
    session.pop('name', None)
    flash('You have successfully logout.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
