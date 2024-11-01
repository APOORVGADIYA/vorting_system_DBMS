from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database helper functions
def get_db():
    db = sqlite3.connect('users.db')
    db.row_factory = sqlite3.Row
    return db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirmPassword']
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('home'))
    
    hashed_password = generate_password_hash(password)
    
    db = get_db()
    try:
        db.execute('INSERT INTO users (email, password) VALUES (?, ?)',
                  (email, hashed_password))
        db.commit()
        flash('Account created successfully! Please login.')
    except sqlite3.IntegrityError:
        flash('Email already exists')
    finally:
        db.close()
    
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    db.close()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['email'] = user['email']
        return redirect(url_for('dashboard'))
    
    flash('Invalid email or password')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    search_query = request.args.get('search', '')
    
    db = get_db()
    if search_query:
        elections = db.execute('''
            SELECT * FROM elections 
            WHERE (title LIKE ? OR description LIKE ?)
            AND created_by = ?
            ORDER BY election_date DESC
        ''', (f'%{search_query}%', f'%{search_query}%', session['user_id'])).fetchall()
    else:
        elections = db.execute('''
            SELECT * FROM elections 
            WHERE created_by = ?
            ORDER BY election_date DESC
        ''', (session['user_id'],)).fetchall()
    db.close()
    
    return render_template('dashboard.html', elections=elections)

@app.route('/election/create', methods=['GET', 'POST'])
@login_required
def create_election():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        election_type = request.form['election_type']
        election_date = request.form['election_date']
        
        db = get_db()
        cursor = db.execute('''
            INSERT INTO elections (title, description, election_type, created_by, election_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, election_type, session['user_id'], election_date))
        election_id = cursor.lastrowid
        db.commit()
        db.close()
        
        flash('Election created successfully!')
        return redirect(url_for('manage_candidates', election_id=election_id))
    
    return render_template('create_election.html')

@app.route('/election/<int:election_id>/delete', methods=['POST'])
@login_required
def delete_election(election_id):
    db = get_db()
    election = db.execute('SELECT * FROM elections WHERE id = ?', (election_id,)).fetchone()
    
    if not election or election['created_by'] != session['user_id']:
        db.close()
        flash('You do not have permission to delete this election')
        return redirect(url_for('dashboard'))
    
    try:
        # Delete associated candidates first
        db.execute('DELETE FROM candidates WHERE election_id = ?', (election_id,))
        # Then delete the election
        db.execute('DELETE FROM elections WHERE id = ?', (election_id,))
        db.commit()
        flash('Election deleted successfully!')
    except Exception as e:
        flash('Error deleting election')
    
    db.close()
    return redirect(url_for('dashboard'))

@app.route('/election/<int:election_id>/candidates', methods=['GET', 'POST'])
@login_required
def manage_candidates(election_id):
    search_query = request.args.get('search', '')
    
    db = get_db()
    election = db.execute('SELECT * FROM elections WHERE id = ?', (election_id,)).fetchone()
    
    if not election:
        db.close()
        flash('Election not found')
        return redirect(url_for('dashboard'))
    
    if election['created_by'] != session['user_id']:
        db.close()
        flash('You do not have permission to manage candidates')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        candidate_name = request.form['candidate_name']
        party_name = request.form['party_name']
        party_tagline = request.form['party_tagline']
        
        try:
            # First, check if party exists or create it
            party = db.execute('SELECT id FROM parties WHERE name = ?', (party_name,)).fetchone()
            if party:
                party_id = party['id']
            else:
                cursor = db.execute('INSERT INTO parties (name, tagline) VALUES (?, ?)',
                                  (party_name, party_tagline))
                party_id = cursor.lastrowid
            
            # Then try to insert the candidate
            db.execute('''
                INSERT INTO candidates (election_id, party_id, name)
                VALUES (?, ?, ?)
            ''', (election_id, party_id, candidate_name))
            db.commit()
            flash('Candidate added successfully!')
        except sqlite3.IntegrityError:
            flash('A candidate with this name already exists in this election')
    
    # Modified query to include search and join with parties
    if search_query:
        candidates = db.execute('''
            SELECT c.*, p.name as party_name, p.tagline as party_tagline 
            FROM candidates c
            JOIN parties p ON c.party_id = p.id
            WHERE c.election_id = ? AND 
                  (c.name LIKE ? OR p.name LIKE ? OR p.tagline LIKE ?)
        ''', (election_id, f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        candidates = db.execute('''
            SELECT c.*, p.name as party_name, p.tagline as party_tagline 
            FROM candidates c
            JOIN parties p ON c.party_id = p.id
            WHERE c.election_id = ?
        ''', (election_id,)).fetchall()
    
    db.close()
    return render_template('manage_candidates.html', election=election, candidates=candidates)

@app.route('/candidate/<int:candidate_id>/update', methods=['POST'])
@login_required
def update_candidate(candidate_id):
    db = get_db()
    
    # First verify permissions
    candidate = db.execute('''
        SELECT c.*, e.created_by, c.election_id
        FROM candidates c 
        JOIN elections e ON c.election_id = e.id 
        WHERE c.id = ?
    ''', (candidate_id,)).fetchone()
    
    if not candidate:
        db.close()
        flash('Candidate not found')
        return redirect(url_for('dashboard'))
    
    if candidate['created_by'] != session['user_id']:
        db.close()
        flash('You do not have permission to update this candidate')
        return redirect(url_for('dashboard'))
    
    candidate_name = request.form['candidate_name']
    party_name = request.form['party_name']
    party_tagline = request.form['party_tagline']
    
    try:
        # Update or create party
        party = db.execute('SELECT id FROM parties WHERE name = ?', (party_name,)).fetchone()
        if party:
            party_id = party['id']
            db.execute('UPDATE parties SET tagline = ? WHERE id = ?',
                      (party_tagline, party_id))
        else:
            cursor = db.execute('INSERT INTO parties (name, tagline) VALUES (?, ?)',
                              (party_name, party_tagline))
            party_id = cursor.lastrowid
        
        # Update candidate
        db.execute('''
            UPDATE candidates 
            SET name = ?, party_id = ?
            WHERE id = ?
        ''', (candidate_name, party_id, candidate_id))
        db.commit()
        flash('Candidate updated successfully!')
    except sqlite3.IntegrityError:
        flash('A candidate with this name already exists in this election')
    
    db.close()
    return redirect(url_for('manage_candidates', election_id=candidate['election_id']))

@app.route('/candidate/<int:candidate_id>/delete', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    db = get_db()
    
    # First verify permissions
    candidate = db.execute('''
        SELECT c.*, e.created_by, c.election_id
        FROM candidates c 
        JOIN elections e ON c.election_id = e.id 
        WHERE c.id = ?
    ''', (candidate_id,)).fetchone()
    
    if not candidate:
        db.close()
        flash('Candidate not found')
        return redirect(url_for('dashboard'))
    
    if candidate['created_by'] != session['user_id']:
        db.close()
        flash('You do not have permission to delete this candidate')
        return redirect(url_for('dashboard'))
    
    election_id = candidate['election_id']
    
    try:
        db.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
        db.commit()
        flash('Candidate deleted successfully!')
    except Exception as e:
        flash('Error deleting candidate')
        
    db.close()
    return redirect(url_for('manage_candidates', election_id=election_id))

@app.route('/election/<int:election_id>/report')
@login_required
def view_report(election_id):
    db = get_db()
    election = db.execute('SELECT * FROM elections WHERE id = ?', (election_id,)).fetchone()
    
    if not election:
        db.close()
        flash('Election not found')
        return redirect(url_for('dashboard'))
    
    if election['created_by'] != session['user_id']:
        db.close()
        flash('You do not have permission to view this report')
        return redirect(url_for('dashboard'))
    
    candidates = db.execute('''
        SELECT c.*, p.name as party_name, p.tagline as party_tagline 
        FROM candidates c
        JOIN parties p ON c.party_id = p.id
        WHERE c.election_id = ?
        ORDER BY c.name
    ''', (election_id,)).fetchall()
    
    db.close()
    return render_template('election_report.html', election=election, candidates=candidates)

if __name__ == '__main__':
    app.run(debug=True)